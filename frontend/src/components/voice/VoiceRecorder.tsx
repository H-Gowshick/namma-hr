import { useEffect, useRef, useState } from "react";

import type { AppLanguageCode } from "../../lib/languages";
import {
  getAppLanguage,
  isVoiceLanguageSupported,
  languageOptionLabel,
  unsupportedVoiceLanguageMessage,
} from "../../lib/languages";
import { IconMic, IconSend, IconStop, IconX } from "../icons";
import { VOICE_HTTP_BASE, voiceWebSocketUrl } from "../../lib/voiceApi";
const TARGET_SAMPLE_RATE = 16000;
const MAX_RECORDING_SECONDS = 12;
const PCM_FRAME_BYTES = 1024;
const FRAME_SAMPLES = PCM_FRAME_BYTES / 2;
const FRAME_INTERVAL_MS = 32;
const REST_TIMEOUT_MS = 45000;
const STREAM_TIMEOUT_MS = 45000;
const SILENCE_THRESHOLD = 0.012;

type VoicePhase = "idle" | "recording" | "processing" | "transcribed" | "error";

type VoiceRecorderProps = {
  language: AppLanguageCode;
  onTranscript?: (text: string) => void;
  assistantSpeaking?: boolean;
};

type TranscriptionResponse = {
  transcript?: string;
  detail?: string | { msg?: string }[];
  detected_language?: string;
  requested_language?: string;
};

type StreamSession = {
  context: AudioContext;
  source: MediaStreamAudioSourceNode;
  processor: ScriptProcessorNode;
  stream: MediaStream;
  ws: WebSocket;
  pcmQueue: Int16Array[];
  pendingSamples: number[];
  heardSpeech: boolean;
  silentFrames: number;
  maxTimer: ReturnType<typeof setTimeout>;
  paceTimer: ReturnType<typeof setInterval>;
  overallTimer: ReturnType<typeof setTimeout>;
  finished: boolean;
};

function detailToMessage(detail: TranscriptionResponse["detail"]): string {
  if (!detail) {
    return "Gnani transcription failed. Please try again.";
  }

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item) => item.msg)
      .filter(Boolean)
      .join(" ");
  }

  return "Gnani transcription failed. Please try again.";
}

function getErrorMessage(error: unknown): string {
  if (error instanceof TypeError) {
    const message = error.message.toLowerCase();

    if (message.includes("failed to fetch") || message.includes("network")) {
      return (
        "Could not reach the voice service on port 8000. " +
        "Make sure the voice API is running, then try again."
      );
    }
  }

  if (error instanceof DOMException) {
    if (error.name === "NotAllowedError" || error.name === "SecurityError") {
      return "Microphone permission denied. Please allow microphone access.";
    }

    if (error.name === "NotFoundError") {
      return "No microphone was found. Please connect a microphone.";
    }

    if (error.name === "NotReadableError") {
      return "Your microphone is being used by another application.";
    }

    if (error.name === "AbortError") {
      return "Speech recognition timed out. Please try a shorter question.";
    }
  }

  return error instanceof Error
    ? error.message
    : "An unexpected error occurred.";
}

function downsampleBuffer(
  samples: Float32Array,
  inputRate: number,
  outputRate: number,
): Float32Array {
  if (outputRate >= inputRate) {
    return samples;
  }

  const ratio = inputRate / outputRate;
  const newLength = Math.max(1, Math.floor(samples.length / ratio));
  const result = new Float32Array(newLength);

  for (let i = 0; i < newLength; i++) {
    const start = Math.floor(i * ratio);
    const end = Math.min(samples.length, Math.floor((i + 1) * ratio));
    let sum = 0;
    let count = 0;

    for (let j = start; j < end; j++) {
      sum += samples[j];
      count += 1;
    }

    result[i] = count > 0 ? sum / count : samples[start] || 0;
  }

  return result;
}

function floatToPcm16(samples: Float32Array): Int16Array {
  const pcm = new Int16Array(samples.length);

  for (let i = 0; i < samples.length; i++) {
    const sample = Math.max(-1, Math.min(1, samples[i]));
    pcm[i] = sample < 0 ? sample * 32768 : sample * 32767;
  }

  return pcm;
}

function createWavBlob(samples: Float32Array, sampleRate: number): Blob {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  function writeString(offset: number, text: string) {
    for (let i = 0; i < text.length; i++) {
      view.setUint8(offset + i, text.charCodeAt(i));
    }
  }

  writeString(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, samples.length * 2, true);

  for (let i = 0; i < samples.length; i++) {
    const sample = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(
      44 + i * 2,
      sample < 0 ? sample * 32768 : sample * 32767,
      true,
    );
  }

  return new Blob([buffer], { type: "audio/wav" });
}

const WAVE_BARS = 28;

export default function VoiceRecorder({
  language,
  onTranscript,
  assistantSpeaking = false,
}: VoiceRecorderProps) {
  const [recording, setRecording] = useState(false);
  const [loading, setLoading] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [levels, setLevels] = useState<number[]>(() =>
    Array.from({ length: WAVE_BARS }, () => 0.08),
  );
  const sessionRef = useRef<StreamSession | null>(null);
  const fallbackChunksRef = useRef<Float32Array[]>([]);
  const mountedRef = useRef(true);
  const languageRef = useRef(language);
  const lastLevelAtRef = useRef(0);

  languageRef.current = language;

  const selectedLanguage = getAppLanguage(language);
  const voiceSupported = isVoiceLanguageSupported(language);

  function cleanupSession(session: StreamSession, closeSocket = true) {
    clearTimeout(session.maxTimer);
    clearTimeout(session.overallTimer);
    clearInterval(session.paceTimer);

    try {
      session.processor.disconnect();
      session.source.disconnect();
    } catch {
      // Already disconnected.
    }

    session.stream.getTracks().forEach((track) => track.stop());

    if (session.context.state !== "closed") {
      void session.context.close().catch(() => {});
    }

    if (
      closeSocket &&
      (session.ws.readyState === WebSocket.OPEN ||
        session.ws.readyState === WebSocket.CONNECTING)
    ) {
      try {
        session.ws.close();
      } catch {
        // Ignore.
      }
    }
  }

  useEffect(() => {
    mountedRef.current = true;

    return () => {
      mountedRef.current = false;
      const session = sessionRef.current;
      if (session) {
        sessionRef.current = null;
        cleanupSession(session);
      }
    };
  }, []);

  useEffect(() => {
    if (!voiceSupported) {
      const session = sessionRef.current;
      if (session) {
        sessionRef.current = null;
        cleanupSession(session);
        setRecording(false);
        setLoading(false);
      }
      setTranscript("");
      setError(unsupportedVoiceLanguageMessage(language));
      return;
    }

    setError((previous) =>
      previous.startsWith("Voice input is not available") ? "" : previous,
    );
  }, [language, voiceSupported]);

  function finishWithTranscript(text: string) {
    const session = sessionRef.current;
    if (session?.finished) {
      return;
    }

    if (session) {
      session.finished = true;
      sessionRef.current = null;
      cleanupSession(session);
    }

    if (!mountedRef.current) {
      return;
    }

    setRecording(false);
    setLoading(false);
    setTranscript(text);
    setNotice("");
    setError("");
  }

  function submitTranscript() {
    const text = transcript.trim();
    if (!text) {
      setError("The transcription is empty. Record again or type your question.");
      return;
    }

    setTranscript("");
    setError("");
    onTranscript?.(text);
  }

  function discardTranscript() {
    setTranscript("");
    setError("");
    setNotice("");
  }

  function cancelRecording() {
    const session = sessionRef.current;
    if (session && !session.finished) {
      session.finished = true;
      sessionRef.current = null;
      cleanupSession(session);
    }

    fallbackChunksRef.current = [];

    if (!mountedRef.current) {
      return;
    }

    setRecording(false);
    setLoading(false);
    setLevels(Array.from({ length: WAVE_BARS }, () => 0.08));
  }

  function finishWithError(message: string) {
    const session = sessionRef.current;
    if (session?.finished) {
      return;
    }

    if (session) {
      session.finished = true;
      sessionRef.current = null;
      cleanupSession(session);
    }

    if (!mountedRef.current) {
      return;
    }

    setRecording(false);
    setLoading(false);
    setTranscript("");
    setError(message);
  }

  function enqueuePcm(session: StreamSession, pcm: Int16Array) {
    for (let i = 0; i < pcm.length; i++) {
      session.pendingSamples.push(pcm[i]);
    }

    while (session.pendingSamples.length >= FRAME_SAMPLES) {
      const frame = new Int16Array(FRAME_SAMPLES);
      for (let i = 0; i < FRAME_SAMPLES; i++) {
        frame[i] = session.pendingSamples.shift() as number;
      }
      session.pcmQueue.push(frame);
    }
  }

  function sendCommit(session: StreamSession) {
    if (session.ws.readyState === WebSocket.OPEN) {
      session.ws.send(JSON.stringify({ type: "commit" }));
    }
  }

  async function transcribeWithRestFallback(
    samples: Float32Array,
    sampleRate: number,
  ) {
    const speechSamples = downsampleBuffer(
      samples,
      sampleRate,
      TARGET_SAMPLE_RATE,
    );
    const wavBlob = createWavBlob(speechSamples, TARGET_SAMPLE_RATE);
    const formData = new FormData();
    formData.append("audio", wavBlob, "recording.wav");
    formData.append("language", languageRef.current);

    const controller = new AbortController();
    const timer = setTimeout(() => {
      controller.abort();
    }, REST_TIMEOUT_MS);

    try {
      const response = await fetch(`${VOICE_HTTP_BASE}/voice/transcribe`, {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });

      let result: TranscriptionResponse;
      try {
        result = await response.json();
      } catch {
        throw new Error("The backend returned an invalid response.");
      }

      if (!response.ok) {
        throw new Error(detailToMessage(result.detail));
      }

      const recognizedText = (result.transcript || "").trim();
      if (!recognizedText) {
        throw new Error("No speech was recognized. Please try again.");
      }

      finishWithTranscript(recognizedText);
    } finally {
      clearTimeout(timer);
    }
  }

  function pushLevel(rms: number) {
    const now = performance.now();
    if (now - lastLevelAtRef.current < 70) {
      return;
    }

    lastLevelAtRef.current = now;
    const height = Math.max(0.08, Math.min(1, rms * 12));
    setLevels((previous) => [...previous.slice(1), height]);
  }

  async function startRecording() {
    if (loading || recording || sessionRef.current) return;

    setError("");
    setNotice("");
    setTranscript("");
    setLevels(Array.from({ length: WAVE_BARS }, () => 0.08));
    fallbackChunksRef.current = [];

    if (!isVoiceLanguageSupported(languageRef.current)) {
      setError(unsupportedVoiceLanguageMessage(languageRef.current));
      return;
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Microphone recording is not supported in this browser.");
      return;
    }

    let stream: MediaStream | null = null;
    let context: AudioContext | null = null;
    let ws: WebSocket | null = null;

    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: TARGET_SAMPLE_RATE,
        },
      });

      if (!mountedRef.current) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }

      try {
        context = new AudioContext({ sampleRate: TARGET_SAMPLE_RATE });
      } catch {
        context = new AudioContext();
      }

      if (context.state === "suspended") {
        await context.resume();
      }

      ws = new WebSocket(voiceWebSocketUrl(languageRef.current));

      await new Promise<void>((resolve, reject) => {
        const openTimer = setTimeout(() => {
          reject(new Error("Realtime speech connection timed out."));
        }, 20000);

        ws!.onopen = () => {
          clearTimeout(openTimer);
          resolve();
        };

        ws!.onerror = () => {
          clearTimeout(openTimer);
          reject(new Error("Could not open realtime speech connection."));
        };
      });

      const source = context.createMediaStreamSource(stream);
      const processor = context.createScriptProcessor(4096, 1, 1);

      const session: StreamSession = {
        context,
        source,
        processor,
        stream,
        ws,
        pcmQueue: [],
        pendingSamples: [],
        heardSpeech: false,
        silentFrames: 0,
        finished: false,
        maxTimer: setTimeout(() => {
          void stopRecording();
        }, MAX_RECORDING_SECONDS * 1000),
        paceTimer: setInterval(() => {
          const active = sessionRef.current;
          if (!active || active.finished) {
            return;
          }

          if (
            active.ws.readyState === WebSocket.OPEN &&
            active.pcmQueue.length > 0
          ) {
            const frame = active.pcmQueue.shift();
            if (frame) {
              const bytes = new Uint8Array(frame.byteLength);
              bytes.set(
                new Uint8Array(
                  frame.buffer,
                  frame.byteOffset,
                  frame.byteLength,
                ),
              );
              active.ws.send(bytes);
            }
          }
        }, FRAME_INTERVAL_MS),
        overallTimer: setTimeout(() => {
          finishWithError(
            "Speech recognition timed out. Please try a shorter question.",
          );
        }, STREAM_TIMEOUT_MS),
      };

      processor.onaudioprocess = (event) => {
        const active = sessionRef.current;
        if (!active || active.finished) {
          return;
        }

        const input = event.inputBuffer.getChannelData(0);
        const copy = new Float32Array(input);
        fallbackChunksRef.current.push(copy);

        let energy = 0;
        for (let i = 0; i < input.length; i++) {
          energy += input[i] * input[i];
        }
        const rms = Math.sqrt(energy / input.length);

        if (rms > SILENCE_THRESHOLD) {
          active.heardSpeech = true;
        pushLevel(rms);
          active.silentFrames = 0;
        } else if (active.heardSpeech) {
          active.silentFrames += 1;
          // ~0.7s of silence after speech → commit early.
          if (active.silentFrames >= 8) {
            active.silentFrames = 0;
            setLoading(true);
            sendCommit(active);
          }
        }

        const downsampled = downsampleBuffer(
          copy,
          active.context.sampleRate,
          TARGET_SAMPLE_RATE,
        );
        enqueuePcm(active, floatToPcm16(downsampled));
      };

      const silentGain = context.createGain();
      silentGain.gain.value = 0;
      source.connect(processor);
      processor.connect(silentGain);
      silentGain.connect(context.destination);

      ws.onmessage = (event) => {
        try {
          const frame = JSON.parse(String(event.data)) as {
            type?: string;
            transcript?: string;
            message?: string;
          };

          if (frame.type === "transcript" && frame.transcript?.trim()) {
            finishWithTranscript(frame.transcript.trim());
            return;
          }

          if (frame.type === "processing") {
            setLoading(true);
            return;
          }

          if (frame.type === "error") {
            const active = sessionRef.current;
            const chunks = fallbackChunksRef.current;

            if (active && !active.finished && chunks.length > 0) {
              const totalLength = chunks.reduce(
                (sum, chunk) => sum + chunk.length,
                0,
              );
              const samples = new Float32Array(totalLength);
              let offset = 0;
              for (const chunk of chunks) {
                samples.set(chunk, offset);
                offset += chunk.length;
              }
              const sampleRate = active.context.sampleRate;
              active.finished = true;
              sessionRef.current = null;
              cleanupSession(active);
              setRecording(false);
              setLoading(true);
              void transcribeWithRestFallback(samples, sampleRate).catch(
                (err) => {
                  if (mountedRef.current) {
                    setLoading(false);
                    setError(getErrorMessage(err));
                  }
                },
              );
              return;
            }

            if (active && !active.finished) {
              active.finished = true;
              sessionRef.current = null;
              cleanupSession(active);
              setRecording(false);
              void startRestRecordingFallback().catch((err) => {
                if (mountedRef.current) {
                  setError(getErrorMessage(err));
                }
              });
              return;
            }

            finishWithError(
              frame.message || "Realtime speech recognition failed.",
            );
          }
        } catch {
          // Ignore malformed frames.
        }
      };

      ws.onclose = () => {
        const active = sessionRef.current;
        if (active && !active.finished && !active.heardSpeech) {
          finishWithError(
            "Speech connection closed before any speech was heard.",
          );
        }
      };

      sessionRef.current = session;
      setRecording(true);
    } catch (err) {
      stream?.getTracks().forEach((track) => track.stop());
      if (context && context.state !== "closed") {
        await context.close().catch(() => {});
      }
      if (ws) {
        try {
          ws.close();
        } catch {
          // Ignore.
        }
      }

      // Fallback: classic REST path if realtime is unavailable.
      try {
        await startRestRecordingFallback();
      } catch (fallbackError) {
        if (mountedRef.current) {
          setError(getErrorMessage(fallbackError));
        }
      }
    }
  }

  async function startRestRecordingFallback() {
    // Used only when websocket setup fails. Keep behavior simple.
    setNotice("Realtime voice is unavailable. Using backup recognition.");

    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });

    const context = new AudioContext();
    const source = context.createMediaStreamSource(stream);
    const processor = context.createScriptProcessor(4096, 1, 1);
    const chunks: Float32Array[] = [];

    processor.onaudioprocess = (event) => {
      chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)));
    };

    const silentGain = context.createGain();
    silentGain.gain.value = 0;
    source.connect(processor);
    processor.connect(silentGain);
    silentGain.connect(context.destination);

    setRecording(true);

    await new Promise((resolve) => setTimeout(resolve, 2500));

    processor.disconnect();
    source.disconnect();
    stream.getTracks().forEach((track) => track.stop());

    const totalLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
    const samples = new Float32Array(totalLength);
    let offset = 0;
    for (const chunk of chunks) {
      samples.set(chunk, offset);
      offset += chunk.length;
    }

    const sampleRate = context.sampleRate;
    await context.close().catch(() => {});
    setRecording(false);
    setLoading(true);

    try {
      await transcribeWithRestFallback(samples, sampleRate);
    } catch (err) {
      setLoading(false);
      setError(getErrorMessage(err));
    }
  }

  async function stopRecording() {
    const session = sessionRef.current;

    if (!session || session.finished) {
      return;
    }

    setRecording(false);
    setLoading(true);
    sendCommit(session);

    // If Gnani does not answer quickly after commit, fall back to REST
    // using the buffered microphone samples.
    window.setTimeout(() => {
      const active = sessionRef.current;
      if (!active || active.finished) {
        return;
      }

      const chunks = fallbackChunksRef.current;
      if (!chunks.length) {
        finishWithError("No speech was detected. Please try again.");
        return;
      }

      const totalLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
      const samples = new Float32Array(totalLength);
      let offset = 0;
      for (const chunk of chunks) {
        samples.set(chunk, offset);
        offset += chunk.length;
      }

      const sampleRate = active.context.sampleRate;
      active.finished = true;
      sessionRef.current = null;
      cleanupSession(active);

      void transcribeWithRestFallback(samples, sampleRate).catch((err) => {
        if (mountedRef.current) {
          setLoading(false);
          setError(getErrorMessage(err));
        }
      });
    }, 2500);
  }

  const phase: VoicePhase = error
    ? "error"
    : recording
      ? "recording"
      : loading
        ? "processing"
        : transcript
          ? "transcribed"
          : "idle";

  const statusLabel = !voiceSupported
    ? unsupportedVoiceLanguageMessage(language)
    : phase === "recording"
      ? `Recording · ${languageOptionLabel(selectedLanguage)}`
      : phase === "processing"
        ? "Processing speech…"
        : phase === "transcribed"
          ? "Review transcription"
          : assistantSpeaking
            ? "Speaking"
            : `Voice · ${languageOptionLabel(selectedLanguage)}`;

  const showPanel =
    phase !== "idle" || Boolean(notice) || assistantSpeaking || !voiceSupported;

  return (
    <div
      className={`voice-recorder is-${phase}${assistantSpeaking ? " is-speaking" : ""}`}
      lang={selectedLanguage.locale}
    >
      {showPanel ? (
        <div
          className="voice-panel"
          role={phase === "error" ? "alert" : "status"}
        >
          <div className="voice-panel-kicker">
            <span className={`voice-phase voice-phase--${phase}`}>
              {assistantSpeaking && phase === "idle" ? "Speaking" : phase}
            </span>
            <span>{statusLabel}</span>
          </div>

          {phase === "recording" ? (
            <div className="voice-wave" aria-hidden="true">
              {levels.map((level, index) => (
                <span
                  key={index}
                  style={{ transform: `scaleY(${level})` }}
                />
              ))}
            </div>
          ) : null}

          {phase === "transcribed" ? (
            <label className="voice-draft">
              <span>Edit before sending</span>
              <textarea
                value={transcript}
                dir="auto"
                lang={selectedLanguage.locale}
                rows={3}
                onChange={(event) => {
                  setTranscript(event.target.value);
                }}
              />
            </label>
          ) : null}

          {notice && phase !== "error" ? (
            <p className="voice-notice">{notice}</p>
          ) : null}

          {phase === "error" ? <p className="voice-error">{error}</p> : null}

          {phase === "recording" ? (
            <div className="voice-actions">
              <button type="button" onClick={() => void stopRecording()}>
                <IconStop size={14} />
                Stop
              </button>
              <button type="button" onClick={cancelRecording}>
                <IconX size={14} />
                Cancel
              </button>
            </div>
          ) : null}

          {phase === "transcribed" ? (
            <div className="voice-actions">
              <button type="button" onClick={submitTranscript}>
                <IconSend size={14} />
                Send
              </button>
              <button type="button" onClick={discardTranscript}>
                <IconX size={14} />
                Discard
              </button>
            </div>
          ) : null}

          {phase === "error" ? (
            <div className="voice-actions">
              <button
                type="button"
                onClick={() => {
                  setError("");
                }}
              >
                Dismiss
              </button>
            </div>
          ) : null}
        </div>
      ) : null}

      <button
        className="voice-mic-button"
        onClick={() => {
          if (recording) {
            void stopRecording();
          } else {
            void startRecording();
          }
        }}
        disabled={loading || !voiceSupported}
        type="button"
        title={statusLabel}
        aria-label={
          recording
            ? "Stop recording"
            : voiceSupported
              ? `Start voice input in ${selectedLanguage.englishName}`
              : "Voice input unavailable for selected language"
        }
      >
        <IconMic size={17} />
        {recording ? <span className="voice-pulse" aria-hidden="true" /> : null}
      </button>
    </div>
  );
}
