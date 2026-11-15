import { useRef, useState } from "react";

import type { ReactNode, WheelEvent } from "react";

import "./App.css";

import ChatMessage from "./components/chat/ChatMessage";
import EvaluationDashboard from "./components/evaluation/EvaluationDashboard";
import PolicyLibrary from "./components/library/PolicyLibrary";
import { useChatStream } from "./hooks/useChatStream";
import { useSpeechPlayback } from "./hooks/useSpeechPlayback";
import LanguageSelector from "./components/LanguageSelector";
import { DEFAULT_LANGUAGE, getAppLanguage, languageOptionLabel } from "./lib/languages";
import {
  IconArrowDown,
  IconBaby,
  IconCalendar,
  IconChart,
  IconFileText,
  IconHeartPulse,
  IconHome,
  IconLibrary,
  IconMenu,
  IconPlus,
  IconSend,
  IconShield,
  IconSparkles,
  IconX,
} from "./components/icons";

import VoiceRecorder from "./components/voice/VoiceRecorder";

type SuggestedQuestion = {
  id: string;
  title: string;
  description: string;
  prompt: string;
  icon: ReactNode;
};

// =========================================================
// CONFIGURATION
// =========================================================

const SUGGESTED_QUESTIONS: SuggestedQuestion[] = [
  {
    id: "casual",
    title: "Casual leave",
    description: "Annual entitlement and monthly limits",
    prompt: "How many casual leave days is an employee entitled to in a year?",
    icon: <IconCalendar size={18} />,
  },
  {
    id: "sick",
    title: "Sick leave",
    description: "Paid days and medical certificates",
    prompt: "How many days of sick leave can an employee take?",
    icon: <IconHeartPulse size={18} />,
  },
  {
    id: "maternity",
    title: "Maternity leave",
    description: "Duration and eligibility rules",
    prompt: "How many weeks of maternity leave are provided?",
    icon: <IconBaby size={18} />,
  },
  {
    id: "wfh",
    title: "Work from home",
    description: "Eligibility and approval guidance",
    prompt: "What is the work from home policy?",
    icon: <IconHome size={18} />,
  },
  {
    id: "adoption",
    title: "Not in the handbook",
    description: "A question the policy does not answer",
    prompt: "How many days of adoption leave does the policy provide?",
    icon: <IconShield size={18} />,
  },
];

// =========================================================
// APP COMPONENT
// =========================================================

function App() {
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [workspace, setWorkspace] = useState<
    "chat" | "library" | "evaluation"
  >("chat");
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState(DEFAULT_LANGUAGE);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [feedbackById, setFeedbackById] = useState<
    Record<string, "helpful" | "not-helpful">
  >({});

  const messagesContainerRef = useRef<HTMLElement>(null);
  const shouldAutoScroll = useRef(true);

  const speech = useSpeechPlayback(selectedLanguage, setError);

  const scrollToBottom = (smooth = false) => {
    const container = messagesContainerRef.current;

    if (!container || !shouldAutoScroll.current) {
      return;
    }

    requestAnimationFrame(() => {
      if (!shouldAutoScroll.current) {
        return;
      }

      container.scrollTo({
        top: container.scrollHeight,
        behavior: smooth ? "smooth" : "auto",
      });
    });
  };

  const {
    messages,
    setMessages,
    input,
    setInput,
    loading,
    setLoading,
    sendMessageText,
    sendMessage,
    sendVoiceMessage,
  } = useChatStream({
    selectedLanguage,
    setError,
    prefetchSpeech: speech.prefetchSpeech,
    scrollToBottom,
    shouldAutoScroll,
    setShowScrollButton,
  });

  const updateScrollState = () => {
    const container = messagesContainerRef.current;

    if (!container) {
      return;
    }

    const distanceFromBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight;

    const atBottom = distanceFromBottom <= 80;

    shouldAutoScroll.current = atBottom;

    setShowScrollButton(!atBottom && loading);
  };

  const handleWheel = (event: WheelEvent<HTMLElement>) => {
    if (event.deltaY < 0) {
      shouldAutoScroll.current = false;

      if (loading) {
        setShowScrollButton(true);
      }
    }
  };

  function startNewChat() {
    speech.releaseSpeech();
    speech.clearSpeechCache();
    setMessages([]);
    setInput("");
    setError(null);
    setLoading(false);
    setShowScrollButton(false);
    setSidebarOpen(false);
  }

  const handleScrollToBottom = () => {
    shouldAutoScroll.current = true;

    setShowScrollButton(false);

    const container = messagesContainerRef.current;

    if (!container) {
      return;
    }

    container.scrollTo({
      top: container.scrollHeight,
      behavior: "smooth",
    });
  };

  const selectedLanguageOption = getAppLanguage(selectedLanguage);
  const hasConversation = messages.length > 0;

  return (
    <div
      className={`app-shell${sidebarOpen ? " app-shell--sidebar-open" : ""}`}
    >
      {sidebarOpen && (
        <button
          type="button"
          className="sidebar-backdrop"
          aria-label="Close navigation"
          onClick={() => {
            setSidebarOpen(false);
          }}
        />
      )}

      <aside className="app-sidebar" aria-label="Namma HR navigation">
        <div className="sidebar-brand">
          <div className="brand-mark" aria-hidden="true">
            <IconShield size={18} />
          </div>
          <div className="brand-copy">
            <span className="brand-name">Namma HR</span>
            <span className="brand-tagline">Policy Assistant</span>
          </div>
          <button
            type="button"
            className="sidebar-close"
            aria-label="Close navigation"
            onClick={() => {
              setSidebarOpen(false);
            }}
          >
            <IconX size={16} />
          </button>
        </div>

        <button
          type="button"
          className="sidebar-new-chat"
          onClick={startNewChat}
        >
          <IconPlus size={16} />
          New chat
        </button>

        <nav className="sidebar-nav" aria-label="Workspace">
          <p className="sidebar-section-label">Workspace</p>
          <button
            type="button"
            className={`sidebar-nav-item${workspace === "chat" ? " is-active" : ""}`}
            onClick={() => {
              setWorkspace("chat");
              setSidebarOpen(false);
            }}
          >
            <IconSparkles size={16} />
            Chat
          </button>
          <button
            type="button"
            className={`sidebar-nav-item${workspace === "library" ? " is-active" : ""}`}
            onClick={() => {
              setWorkspace("library");
              setSidebarOpen(false);
            }}
          >
            <IconLibrary size={16} />
            Policy library
          </button>
          <button
            type="button"
            className={`sidebar-nav-item${workspace === "evaluation" ? " is-active" : ""}`}
            onClick={() => {
              setWorkspace("evaluation");
              setSidebarOpen(false);
            }}
          >
            <IconChart size={16} />
            Evaluation
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-meta">
            <IconFileText size={14} />
            <span>Answers cite your HR policy PDF</span>
          </div>
        </div>
      </aside>

      <div className="chat-app">
        <header className="chat-header">
          <div className="chat-header-inner">
            <div className="chat-header-leading">
              <button
                type="button"
                className="header-menu"
                aria-label="Open navigation"
                onClick={() => {
                  setSidebarOpen(true);
                }}
              >
                <IconMenu size={18} />
              </button>

              <div className="chat-header-titles">
                <p className="chat-header-kicker">
                  {workspace === "library"
                    ? "Library"
                    : workspace === "evaluation"
                      ? "Evaluation"
                      : hasConversation
                        ? "Conversation"
                        : "Home"}
                </p>
                <h1>
                  {workspace === "library"
                    ? "HR Policy Library"
                    : workspace === "evaluation"
                      ? "AI evaluation"
                      : hasConversation
                        ? "HR policy chat"
                        : "Enterprise HR policy assistant"}
                </h1>
              </div>
            </div>

            <div className="chat-header-actions">
              <LanguageSelector
                id="header-language-selector"
                value={selectedLanguage}
                onChange={setSelectedLanguage}
              />
            </div>
          </div>
        </header>

        <main
          ref={messagesContainerRef}
          className="chat-messages"
          onScroll={updateScrollState}
          onWheel={handleWheel}
          aria-live="polite"
        >
          <div className="chat-content">
            {workspace === "evaluation" ? <EvaluationDashboard /> : null}

            {workspace === "library" ? (
              <PolicyLibrary
                askingDisabled={loading}
                onAsk={(prompt) => {
                  setWorkspace("chat");
                  setSidebarOpen(false);
                  void sendMessageText(prompt);
                }}
              />
            ) : null}

            {workspace === "chat" && !hasConversation && (
              <section className="welcome-screen" aria-label="Welcome">
                <div className="welcome-hero">
                  <div className="welcome-badge">
                    <IconSparkles size={14} />
                    Grounded in your HR handbook
                  </div>
                  <h2>Ask the handbook. See the evidence.</h2>
                  <p>
                    Namma HR answers leave and work-from-home questions from the
                    uploaded policy PDF, in the language you select. Each answer
                    can show the retrieved passage and page. Voice uses Gnani
                    for speech in and speech out.
                  </p>
                </div>

                <div className="suggestion-grid">
                  {SUGGESTED_QUESTIONS.map((question) => (
                    <button
                      key={question.id}
                      type="button"
                      className="suggestion-card"
                      disabled={loading}
                      onClick={() => {
                        void sendMessageText(question.prompt);
                      }}
                    >
                      <span className="suggestion-icon">{question.icon}</span>
                      <span className="suggestion-copy">
                        <strong>{question.title}</strong>
                        <span>{question.description}</span>
                      </span>
                    </button>
                  ))}
                </div>
              </section>
            )}

            {workspace === "chat" &&
              messages.map((message, messageIndex) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  messages={messages}
                  messageIndex={messageIndex}
                  selectedLanguage={selectedLanguage}
                  loading={loading}
                  isLatest={message.id === messages[messages.length - 1]?.id}
                  preparingSpeechId={speech.preparingSpeechId}
                  speakingMessageId={speech.speakingMessageId}
                  playbackState={speech.playbackState}
                  replayMessageId={speech.replayMessageId}
                  copiedMessageId={copiedMessageId}
                  feedback={feedbackById[message.id]}
                  onSpeak={(item) => {
                    void speech.speakMessage(item);
                  }}
                  onReplay={(item) => {
                    speech.replaySpeech(item);
                  }}
                  onStopSpeech={speech.stopSpeech}
                  onCopy={(item) => {
                    void navigator.clipboard
                      .writeText(item.content)
                      .then(() => {
                        setCopiedMessageId(item.id);
                        window.setTimeout(() => {
                          setCopiedMessageId((current) =>
                            current === item.id ? null : current,
                          );
                        }, 1600);
                      })
                      .catch(() => {
                        setError("Could not copy the answer.");
                      });
                  }}
                  onFeedback={(messageId, value) => {
                    setFeedbackById((current) => ({
                      ...current,
                      [messageId]: value,
                    }));
                  }}
                  onFollowUp={(prompt) => {
                    void sendMessageText(prompt);
                  }}
                />
              ))}
          </div>
        </main>

        {workspace === "chat" && showScrollButton && (
          <button
            type="button"
            className="scroll-to-bottom"
            onClick={handleScrollToBottom}
            aria-label="Scroll to latest response"
          >
            <IconArrowDown size={15} />
            <span>Latest response</span>
          </button>
        )}

        {error && (
          <div className="chat-error" role="alert">
            {error}
          </div>
        )}

        {workspace === "chat" ? (
          <form className="chat-input" onSubmit={sendMessage}>
            <div className="chat-input-shell">
              <div className="chat-input-inner">
                <input
                  type="text"
                  value={input}
                  onChange={(event) => {
                    setInput(event.target.value);
                  }}
                  placeholder="Ask about leave, WFH, or any HR policy..."
                  disabled={loading}
                  lang={selectedLanguageOption.locale}
                  dir="auto"
                  aria-label="Message"
                />

                <VoiceRecorder
                  language={selectedLanguage}
                  assistantSpeaking={Boolean(speech.speakingMessageId)}
                  onTranscript={sendVoiceMessage}
                />

                <button
                  type="submit"
                  className="send-button"
                  disabled={loading || !input.trim()}
                  aria-label="Send message"
                >
                  {loading ? (
                    <span className="send-spinner" />
                  ) : (
                    <IconSend size={16} />
                  )}
                </button>
              </div>
              <p className="composer-hint">
                Answering in {languageOptionLabel(selectedLanguageOption)}
              </p>
            </div>
          </form>
        ) : null}
      </div>
    </div>
  );
}

export default App;
