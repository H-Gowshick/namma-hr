import { Streamdown } from "streamdown";
import "streamdown/styles.css";

import EvidenceExplorer from "../evidence/EvidenceExplorer";
import { followUpSuggestions } from "../../lib/followUpSuggestions";
import {
  IconBot,
  IconCheck,
  IconCopy,
  IconPause,
  IconStop,
  IconUser,
  IconVolume,
} from "../icons";
import {
  getAppLanguage,
  isTtsLanguageSupported,
  languageOptionLabel,
  unsupportedTtsLanguageMessage,
} from "../../lib/languages";
import { messageTextDirection } from "../../lib/messageDirection";
import { normalizeMessageText } from "../../lib/normalizeMessageText";
import type { Message } from "../../lib/chatTypes";

type ChatMessageProps = {
  message: Message;
  messages: Message[];
  messageIndex: number;
  selectedLanguage: Message["language"];
  loading: boolean;
  isLatest: boolean;
  preparingSpeechId: string | null;
  speakingMessageId: string | null;
  playbackState: "idle" | "playing" | "paused";
  replayMessageId: string | null;
  copiedMessageId: string | null;
  feedback: "helpful" | "not-helpful" | undefined;
  onSpeak: (message: Message) => void;
  onReplay: (message: Message) => void;
  onStopSpeech: () => void;
  onCopy: (message: Message) => void;
  onFeedback: (messageId: string, value: "helpful" | "not-helpful") => void;
  onFollowUp: (prompt: string) => void;
};

export default function ChatMessage({
  message,
  messages,
  messageIndex,
  selectedLanguage,
  loading,
  isLatest,
  preparingSpeechId,
  speakingMessageId,
  playbackState,
  replayMessageId,
  copiedMessageId,
  feedback,
  onSpeak,
  onReplay,
  onStopSpeech,
  onCopy,
  onFeedback,
  onFollowUp,
}: ChatMessageProps) {
  const messageLanguage = message.language ?? selectedLanguage;
  const messageLocale = getAppLanguage(messageLanguage).locale;
  const direction = messageTextDirection(message.content);
  const contentLanguage = direction === "rtl" ? "ur" : messageLocale;
  const voiceLanguage = getAppLanguage(messageLanguage);
  const priorUserPrompt =
    message.role === "assistant"
      ? ([...messages.slice(0, messageIndex)]
          .reverse()
          .find((entry) => entry.role === "user")?.content ?? "")
      : "";
  const isStreaming = loading && message.role === "assistant" && isLatest;

  return (
    <article
      className={`message message--${message.role}${isStreaming ? " message--streaming" : ""}`}
      lang={messageLocale}
    >
      <div className="message-avatar" aria-hidden="true">
        {message.role === "user" ? (
          <IconUser size={15} />
        ) : (
          <IconBot size={15} />
        )}
      </div>

      <div className="message-body">
        <div className="message-label">
          {message.role === "user" ? "You" : "Namma HR"}
          {" · "}
          {languageOptionLabel(voiceLanguage)}
          {isStreaming ? (
            <span className="message-streaming-label">Responding</span>
          ) : null}
        </div>

        {message.content ? (
          <div className="message-content" dir={direction} lang={contentLanguage}>
            <Streamdown>{normalizeMessageText(message.content)}</Streamdown>
          </div>
        ) : isStreaming ? (
          <div className="typing-indicator" aria-label="Assistant is responding">
            <span />
            <span />
            <span />
          </div>
        ) : null}

        {message.role === "assistant" && message.evidenceReady && !isStreaming ? (
          <EvidenceExplorer
            items={message.evidence ?? []}
            ready={true}
            highlightQuery={priorUserPrompt}
          />
        ) : null}

        {message.role === "assistant" && message.content ? (
          <div className="speech-controls">
            {preparingSpeechId === message.id ? (
              <span className="speech-indicator">Preparing voice</span>
            ) : null}
            {playbackState === "playing" && speakingMessageId === message.id ? (
              <span className="speech-indicator is-speaking">Speaking</span>
            ) : null}
            {playbackState === "paused" && replayMessageId === message.id ? (
              <span className="speech-indicator">Paused</span>
            ) : null}

            <button
              type="button"
              className={`speak-button${speakingMessageId === message.id || preparingSpeechId === message.id ? " is-active" : ""}`}
              onClick={() => {
                onSpeak(message);
              }}
              disabled={
                !isTtsLanguageSupported(messageLanguage) ||
                (loading &&
                  preparingSpeechId !== message.id &&
                  speakingMessageId !== message.id)
              }
              title={
                isTtsLanguageSupported(messageLanguage)
                  ? `Listen in ${voiceLanguage.englishName}`
                  : unsupportedTtsLanguageMessage(messageLanguage)
              }
            >
              {preparingSpeechId === message.id ? (
                <>
                  <span className="send-spinner" />
                  Preparing
                </>
              ) : playbackState === "playing" &&
                speakingMessageId === message.id ? (
                <>
                  <IconPause size={14} />
                  Pause
                </>
              ) : (
                <>
                  <IconVolume size={14} />
                  {isTtsLanguageSupported(messageLanguage)
                    ? replayMessageId === message.id
                      ? "Play"
                      : "Listen"
                    : "Unavailable"}
                </>
              )}
            </button>

            {replayMessageId === message.id && preparingSpeechId !== message.id ? (
              <>
                <button
                  type="button"
                  className="speak-button"
                  onClick={() => {
                    onReplay(message);
                  }}
                >
                  Replay
                </button>
                <button type="button" className="speak-button" onClick={onStopSpeech}>
                  <IconStop size={14} />
                  Stop
                </button>
              </>
            ) : null}
          </div>
        ) : null}

        {message.role === "assistant" && message.content && !isStreaming ? (
          <div className="answer-tools">
            <button
              type="button"
              className="speak-button"
              onClick={() => {
                onCopy(message);
              }}
            >
              {copiedMessageId === message.id ? (
                <IconCheck size={14} />
              ) : (
                <IconCopy size={14} />
              )}
              {copiedMessageId === message.id ? "Copied" : "Copy"}
            </button>
            <button
              type="button"
              className={`speak-button${feedback === "helpful" ? " is-selected" : ""}`}
              aria-pressed={feedback === "helpful"}
              onClick={() => {
                onFeedback(message.id, "helpful");
              }}
            >
              Helpful
            </button>
            <button
              type="button"
              className={`speak-button${feedback === "not-helpful" ? " is-selected" : ""}`}
              aria-pressed={feedback === "not-helpful"}
              onClick={() => {
                onFeedback(message.id, "not-helpful");
              }}
            >
              Not helpful
            </button>
            {feedback ? (
              <span className="answer-feedback-note">Saved on this screen only.</span>
            ) : null}
          </div>
        ) : null}

        {message.role === "assistant" &&
        !isStreaming &&
        isLatest &&
        priorUserPrompt ? (
          <div className="follow-ups">
            <p>Follow-up questions</p>
            <div>
              {followUpSuggestions(priorUserPrompt).map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  disabled={loading}
                  onClick={() => {
                    onFollowUp(prompt);
                  }}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </article>
  );
}
