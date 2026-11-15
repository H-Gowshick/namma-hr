import { useState } from "react";

import type { FormEvent, MutableRefObject } from "react";

import { apiUrl } from "../lib/apiBase";
import type { ChatApiMessage, Message } from "../lib/chatTypes";
import type { EvidenceItem } from "../lib/evidenceTypes";
import type { AppLanguageCode } from "../lib/languages";
import { parseEvidenceStream } from "../lib/parseEvidenceStream";
import { createStreamReveal } from "../lib/streamReveal";

type UseChatStreamOptions = {
  selectedLanguage: AppLanguageCode;
  setError: (message: string | null) => void;
  prefetchSpeech: (message: Message) => void;
  scrollToBottom: (smooth?: boolean) => void;
  shouldAutoScroll: MutableRefObject<boolean>;
  setShowScrollButton: (visible: boolean) => void;
};

export function useChatStream({
  selectedLanguage,
  setError,
  prefetchSpeech,
  scrollToBottom,
  shouldAutoScroll,
  setShowScrollButton,
}: UseChatStreamOptions) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function sendMessageText(text: string) {
    const trimmedText = text.trim();

    if (!trimmedText || loading) {
      return;
    }

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmedText,
      language: selectedLanguage,
    };

    const assistantId = crypto.randomUUID();

    const history = messages.filter((message) => message.content.trim() !== "");

    setMessages((previous) => [
      ...previous,
      userMessage,
      {
        id: assistantId,
        role: "assistant",
        content: "",
        language: selectedLanguage,
        evidenceReady: false,
      },
    ]);

    setInput("");
    setError(null);
    setLoading(true);

    shouldAutoScroll.current = true;

    requestAnimationFrame(() => {
      scrollToBottom(true);
    });

    let streamedRaw = "";
    let streamedAnswer = "";
    let visibleAnswer = "";
    let evidenceItems: EvidenceItem[] | undefined;
    let evidenceReady = false;

    const reveal = createStreamReveal({
      charsPerTick: 4,
      tickMs: 16,
      onUpdate(text) {
        visibleAnswer = text;
        setMessages((previous) =>
          previous.map((message) =>
            message.id === assistantId
              ? {
                  ...message,
                  content: text,
                  evidence: evidenceItems,
                  evidenceReady,
                }
              : message,
          ),
        );
        scrollToBottom();
      },
    });

    try {
      const requestMessages: ChatApiMessage[] = [...history, userMessage].map(
        (message) => ({
          role: message.role,
          content: message.content,
        }),
      );

      const response = await fetch(apiUrl("/chat"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/plain",
        },
        body: JSON.stringify({
          message: requestMessages,
          language: selectedLanguage,
        }),
        signal: AbortSignal.timeout(90000),
      });

      if (!response.ok) {
        let errorMessage = `Server error: ${response.status}`;

        try {
          const errorData = (await response.json()) as {
            detail?: string;
            error?: string;
          };

          errorMessage = errorData.detail ?? errorData.error ?? errorMessage;
        } catch {
          // Use fallback error.
        }

        throw new Error(errorMessage);
      }

      if (!response.body) {
        throw new Error(
          "The server did not provide a readable response stream.",
        );
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          break;
        }

        streamedRaw += decoder.decode(value, {
          stream: true,
        });

        const parsed = parseEvidenceStream(streamedRaw);
        streamedAnswer = parsed.answer;
        evidenceReady = parsed.evidenceReady;
        evidenceItems = parsed.evidence ?? undefined;

        setMessages((previous) =>
          previous.map((message) =>
            message.id === assistantId
              ? {
                  ...message,
                  content: visibleAnswer,
                  evidence: evidenceItems,
                  evidenceReady,
                }
              : message,
          ),
        );

        if (streamedAnswer) {
          reveal.push(streamedAnswer);
        }
      }

      streamedRaw += decoder.decode();
      const parsed = parseEvidenceStream(streamedRaw);
      streamedAnswer = parsed.answer;
      evidenceReady = parsed.evidenceReady;
      evidenceItems = parsed.evidence ?? undefined;

      if (streamedAnswer) {
        reveal.push(streamedAnswer);
      }

      await reveal.finish();

      setMessages((previous) =>
        previous.map((message) =>
          message.id === assistantId
            ? {
                ...message,
                content: streamedAnswer,
                evidence: evidenceItems,
                evidenceReady,
              }
            : message,
        ),
      );

      if (!streamedAnswer.trim()) {
        throw new Error("The server returned an empty response.");
      }

      const failureText = streamedAnswer.trim().toLowerCase();
      if (
        failureText.includes("rate limit") ||
        failureText.includes("token limit") ||
        failureText.includes("chat request failed")
      ) {
        setError(streamedAnswer.trim());
        return;
      }

      prefetchSpeech({
        id: assistantId,
        role: "assistant",
        content: streamedAnswer,
        language: selectedLanguage,
        evidence: evidenceItems,
        evidenceReady,
      });
    } catch (err) {
      console.error("CHAT STREAM ERROR:", err);
      reveal.cancel();

      const timedOut =
        err instanceof DOMException &&
        (err.name === "TimeoutError" || err.name === "AbortError");
      setError(
        timedOut
          ? "The answer took too long. Please try the question again."
          : err instanceof Error
            ? err.message
            : "Something went wrong.",
      );

      setMessages((previous) =>
        previous.filter(
          (message) =>
            message.id !== assistantId ||
            visibleAnswer.trim() !== "" ||
            streamedAnswer.trim() !== "",
        ),
      );
    } finally {
      setLoading(false);
      setShowScrollButton(false);
    }
  }

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await sendMessageText(input);
  }

  function sendVoiceMessage(text: string) {
    if (!text.trim()) {
      return;
    }

    void sendMessageText(text);
  }

  return {
    messages,
    setMessages,
    input,
    setInput,
    loading,
    setLoading,
    sendMessageText,
    sendMessage,
    sendVoiceMessage,
  };
}
