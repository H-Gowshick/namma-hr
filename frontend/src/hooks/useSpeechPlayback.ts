import { useEffect, useRef, useState } from "react";

import type { Message } from "../lib/chatTypes";
import {
  getAppLanguage,
  isTtsLanguageSupported,
  unsupportedTtsLanguageMessage,
  type AppLanguageCode,
} from "../lib/languages";
import { toSpeakableText } from "../lib/speakableText";
import { VOICE_HTTP_BASE } from "../lib/voiceApi";

const TTS_API_URL = VOICE_HTTP_BASE;

export function useSpeechPlayback(
  selectedLanguage: AppLanguageCode,
  setError: (message: string | null) => void,
) {
  const [speakingMessageId, setSpeakingMessageId] = useState<string | null>(
    null,
  );
  const [preparingSpeechId, setPreparingSpeechId] = useState<string | null>(
    null,
  );
  const [playbackState, setPlaybackState] = useState<
    "idle" | "playing" | "paused"
  >("idle");
  const [replayMessageId, setReplayMessageId] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlRef = useRef<string | null>(null);
  const ttsCacheRef = useRef<Map<string, Blob>>(new Map());
  const ttsAbortRef = useRef<AbortController | null>(null);
  const prefetchAbortRef = useRef<AbortController | null>(null);

  const releaseSpeech = () => {
    ttsAbortRef.current?.abort();
    ttsAbortRef.current = null;

    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = "";
      audioRef.current = null;
    }

    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
    }

    setSpeakingMessageId(null);
    setPreparingSpeechId(null);
    setPlaybackState("idle");
    setReplayMessageId(null);
  };

  const stopSpeech = () => {
    ttsAbortRef.current?.abort();
    ttsAbortRef.current = null;

    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }

    setSpeakingMessageId(null);
    setPreparingSpeechId(null);
    setPlaybackState("idle");
  };

  function pauseSpeech() {
    audioRef.current?.pause();
    setPlaybackState("paused");
    setSpeakingMessageId(null);
  }

  async function resumeSpeech(messageId: string) {
    const audio = audioRef.current;
    if (!audio || replayMessageId !== messageId) {
      return;
    }

    setSpeakingMessageId(messageId);
    setPlaybackState("playing");
    await audio.play();
  }

  function ttsCacheKey(message: Message): string {
    return `${message.id}:${message.language}:${toSpeakableText(message.content)}`;
  }

  async function fetchSpeechAudio(
    message: Message,
    signal?: AbortSignal,
  ): Promise<Blob> {
    const cacheKey = ttsCacheKey(message);
    const cached = ttsCacheRef.current.get(cacheKey);

    if (cached) {
      return cached;
    }

    const messageLanguage = message.language ?? selectedLanguage;
    const languageConfig = getAppLanguage(messageLanguage);
    const speakable = toSpeakableText(message.content);

    if (!speakable) {
      throw new Error("There is no speakable text in this answer.");
    }

    const response = await fetch(`${TTS_API_URL}/voice/speak`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      signal,
      body: JSON.stringify({
        text: speakable,
        language: messageLanguage,
        voice: languageConfig.ttsVoice,
      }),
    });

    if (!response.ok) {
      let errorMessage = `TTS error: ${response.status}`;

      try {
        const errorData = await response.json();

        if (errorData.detail) {
          errorMessage =
            typeof errorData.detail === "string"
              ? errorData.detail
              : errorMessage;
        }
      } catch {
        // Keep fallback error message.
      }

      throw new Error(errorMessage);
    }

    const audioBlob = await response.blob();

    if (!audioBlob.size) {
      throw new Error("Gnani returned empty audio.");
    }

    ttsCacheRef.current.set(cacheKey, audioBlob);

    if (ttsCacheRef.current.size > 24) {
      const oldest = ttsCacheRef.current.keys().next().value;
      if (oldest) {
        ttsCacheRef.current.delete(oldest);
      }
    }

    return audioBlob;
  }

  function prefetchSpeech(message: Message) {
    const messageLanguage = message.language ?? selectedLanguage;

    if (
      message.role !== "assistant" ||
      !message.content.trim() ||
      !isTtsLanguageSupported(messageLanguage)
    ) {
      return;
    }

    const cacheKey = ttsCacheKey(message);

    if (ttsCacheRef.current.has(cacheKey)) {
      return;
    }

    prefetchAbortRef.current?.abort();
    const controller = new AbortController();
    prefetchAbortRef.current = controller;

    void fetchSpeechAudio(message, controller.signal).catch((err) => {
      if (err instanceof DOMException && err.name === "AbortError") {
        return;
      }
      console.warn("TTS prefetch skipped:", err);
    });
  }

  function clearSpeechCache() {
    prefetchAbortRef.current?.abort();
    ttsCacheRef.current.clear();
  }

  useEffect(() => {
    return () => {
      ttsAbortRef.current?.abort();
      prefetchAbortRef.current?.abort();

      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = "";
      }

      if (audioUrlRef.current) {
        URL.revokeObjectURL(audioUrlRef.current);
      }
    };
  }, []);

  async function speakMessage(message: Message) {
    if (!message.content.trim()) {
      setError("There is no text to speak.");
      return;
    }

    if (preparingSpeechId === message.id) {
      releaseSpeech();
      return;
    }

    if (playbackState === "playing" && speakingMessageId === message.id) {
      pauseSpeech();
      return;
    }

    if (
      audioRef.current &&
      replayMessageId === message.id &&
      playbackState !== "playing"
    ) {
      await resumeSpeech(message.id);
      return;
    }

    const messageLanguage = message.language ?? selectedLanguage;

    if (!isTtsLanguageSupported(messageLanguage)) {
      setError(unsupportedTtsLanguageMessage(messageLanguage));
      return;
    }

    releaseSpeech();
    setError(null);
    setPreparingSpeechId(message.id);

    const controller = new AbortController();
    ttsAbortRef.current = controller;

    try {
      const audioBlob = await fetchSpeechAudio(message, controller.signal);

      if (controller.signal.aborted) {
        return;
      }

      const audioUrl = URL.createObjectURL(audioBlob);
      audioUrlRef.current = audioUrl;

      const audio = new Audio(audioUrl);
      audioRef.current = audio;
      setPreparingSpeechId(null);
      setSpeakingMessageId(message.id);
      setReplayMessageId(message.id);
      setPlaybackState("playing");

      audio.onended = () => {
        if (audioRef.current === audio) {
          setSpeakingMessageId(null);
          setPlaybackState("idle");
        }
      };

      audio.onerror = () => {
        releaseSpeech();
        setError("Could not play the generated audio.");
      };

      await audio.play();
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        return;
      }

      console.error("TTS playback error:", err);
      releaseSpeech();

      const messageText =
        err instanceof TypeError
          ? "Could not reach the voice service on port 8000. Make sure it is running."
          : err instanceof Error
            ? err.message
            : "Could not generate speech.";

      setError(messageText);
    }
  }

  function replaySpeech(message: Message) {
    const audio = audioRef.current;
    if (!audio) {
      void speakMessage(message);
      return;
    }
    audio.currentTime = 0;
    setSpeakingMessageId(message.id);
    setPlaybackState("playing");
    void audio.play();
  }

  return {
    speakingMessageId,
    preparingSpeechId,
    playbackState,
    replayMessageId,
    speakMessage,
    stopSpeech,
    releaseSpeech,
    prefetchSpeech,
    clearSpeechCache,
    replaySpeech,
  };
}
