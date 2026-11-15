import { useMemo, useState } from "react";

import {
  evaluationCases,
  evaluationSnapshot,
  failedCases,
  languageCoverage,
  overallLabel,
  overallStatus,
  ratioLabel,
  unavailableRagMetrics,
  voiceRows,
  type OverallStatus,
} from "../../lib/evaluationMetrics";

import "./EvaluationDashboard.css";

const summary = evaluationSnapshot.summary;

function MetricCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <article className="eval-metric">
      <p>{label}</p>
      <strong>{value}</strong>
      <span>{detail}</span>
    </article>
  );
}

function StatusPill({ status }: { status: OverallStatus | "not-evaluated" }) {
  const label =
    status === "not-evaluated" ? "Not evaluated" : overallLabel(status);

  return <span className={`eval-pill eval-pill--${status}`}>{label}</span>;
}

export default function EvaluationDashboard() {
  const [language, setLanguage] = useState("all");
  const [topic, setTopic] = useState("all");
  const [result, setResult] = useState("all");

  const topics = useMemo(
    () => [...new Set(evaluationCases.map((row) => row.title))].sort(),
    [],
  );
  const languages = useMemo(
    () =>
      [...new Map(evaluationCases.map((row) => [row.language, row.languageName]))],
    [],
  );
  const coverage = useMemo(() => languageCoverage(), []);
  const failures = useMemo(() => failedCases(), []);

  const filtered = evaluationCases.filter((row) => {
    if (language !== "all" && row.language !== language) {
      return false;
    }
    if (topic !== "all" && row.title !== topic) {
      return false;
    }
    if (result !== "all" && overallStatus(row) !== result) {
      return false;
    }
    return true;
  });

  const factFailures = failures.filter(
    (row) => overallStatus(row) === "fact-failed",
  );
  const callFailures = failures.filter(
    (row) => overallStatus(row) === "call-failed",
  );
  const interfaceVoice = voiceRows.filter((row) => !row.note);
  const unsupportedVoice = voiceRows.filter((row) => row.note);

  return (
    <div className="eval-dashboard">
      <header className="eval-hero">
        <p className="eval-kicker">AI intelligence</p>
        <h2>Evaluation dashboard</h2>
        <p>
          Figures come from {evaluationSnapshot.sourceFile}, scored against{" "}
          {evaluationSnapshot.sourcePdf}. Counts are shown as correct/scored.
          Metrics the suite does not calculate stay marked Not evaluated.
        </p>
        <ul className="eval-method">
          <li>
            Retrieval passes when a returned passage is the expected PDF page
            and contains the expected wording, or when an out-of-policy topic
            is absent.
          </li>
          <li>
            Answer and citation scores run only after the chat model returns
            text. A failed model call is counted separately and is not treated
            as a correct answer.
          </li>
          <li>
            Speech rows record configured Gnani language codes. They do not
            include microphone or speaker pass/fail results, except the English
            and Tamil voices already noted in the project voice mapping.
          </li>
        </ul>
      </header>

      <section aria-label="Overview">
        <h3>Overview</h3>
        <div className="eval-metric-grid">
          <MetricCard
            label="Test cases"
            value={String(summary.cases)}
            detail="9 languages × 10 policy topics"
          />
          <MetricCard
            label="Retrieval correctness"
            value={ratioLabel(summary.retrieval_correct, summary.cases)}
            detail="Expected page and wording, or absence for out-of-policy"
          />
          <MetricCard
            label="Answer correctness"
            value={ratioLabel(
              summary.answer_factually_correct,
              summary.facts_scored,
            )}
            detail={`${summary.answers_failed} model calls were not scored`}
          />
          <MetricCard
            label="Citation correctness"
            value={ratioLabel(
              summary.citations_correct,
              summary.citations_scored,
            )}
            detail="Scored only when an answer was returned"
          />
          <MetricCard
            label="Languages evaluated"
            value={String(languages.length)}
            detail="Retrieval run for every interface language"
          />
          <MetricCard
            label="Voice audio verified"
            value="2 TTS"
            detail="English and Tamil playback noted in project voice mapping. STT audio is not in this report."
          />
        </div>
      </section>

      <section aria-label="RAG performance">
        <h3>RAG performance</h3>
        <div className="eval-bars">
          <div>
            <div className="eval-bar-label">
              <span>Retrieval correctness</span>
              <span>{ratioLabel(summary.retrieval_correct, summary.cases)}</span>
            </div>
            <div className="eval-bar">
              <span style={{ width: "100%" }} />
            </div>
          </div>
          <div>
            <div className="eval-bar-label">
              <span>Answer correctness</span>
              <span>
                {ratioLabel(
                  summary.answer_factually_correct,
                  summary.facts_scored,
                )}
              </span>
            </div>
            <div className="eval-bar">
              <span
                style={{
                  width: `${(summary.answer_factually_correct / summary.facts_scored) * 100}%`,
                }}
              />
            </div>
          </div>
          <div>
            <div className="eval-bar-label">
              <span>Citation correctness</span>
              <span>
                {ratioLabel(summary.citations_correct, summary.citations_scored)}
              </span>
            </div>
            <div className="eval-bar">
              <span style={{ width: "100%" }} />
            </div>
          </div>
          <div>
            <div className="eval-bar-label">
              <span>Answer language match</span>
              <span>
                {ratioLabel(
                  summary.answer_language_correct,
                  summary.answers_scored,
                )}
              </span>
            </div>
            <div className="eval-bar">
              <span style={{ width: "100%" }} />
            </div>
          </div>
        </div>
        <ul className="eval-unavailable">
          {unavailableRagMetrics.map((metric) => (
            <li key={metric}>
              <strong>{metric}</strong>
              <span>Not evaluated</span>
            </li>
          ))}
        </ul>
      </section>

      <section aria-label="Multilingual coverage">
        <h3>Multilingual coverage</h3>
        <div className="eval-table-wrap">
          <table>
            <thead>
              <tr>
                <th>Language</th>
                <th>UI</th>
                <th>Text answers</th>
                <th>Retrieval</th>
                <th>STT</th>
                <th>TTS</th>
              </tr>
            </thead>
            <tbody>
              {coverage.map((row) => (
                <tr key={row.code}>
                  <td>{row.name}</td>
                  <td>Available</td>
                  <td>
                    {row.textAnswersScored} scored, {row.textAnswersUnscored}{" "}
                    not evaluated
                  </td>
                  <td>
                    {row.retrievalCorrect}/{row.retrievalTested} correct
                  </td>
                  <td>
                    {row.sttConfigured
                      ? "Configured. Audio test not in report."
                      : "Unsupported"}
                  </td>
                  <td>
                    {row.ttsAudioVerified
                      ? "Audio verified"
                      : row.ttsConfigured
                        ? "Configured. Not yet audio-tested."
                        : "Unsupported"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section aria-label="Evaluation results">
        <h3>Evaluation results</h3>
        <div className="eval-filters">
          <label>
            Language
            <select
              value={language}
              onChange={(event) => setLanguage(event.target.value)}
            >
              <option value="all">All</option>
              {languages.map(([code, name]) => (
                <option key={code} value={code}>
                  {name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Topic
            <select value={topic} onChange={(event) => setTopic(event.target.value)}>
              <option value="all">All</option>
              {topics.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          <label>
            Result
            <select
              value={result}
              onChange={(event) => setResult(event.target.value)}
            >
              <option value="all">All</option>
              <option value="pass">Pass</option>
              <option value="fact-failed">Fact check failed</option>
              <option value="call-failed">Model call failed</option>
              <option value="answer-not-evaluated">Answer not evaluated</option>
            </select>
          </label>
        </div>

        {filtered.length === 0 ? (
          <p className="eval-empty">No evaluation rows match these filters.</p>
        ) : (
          <div className="eval-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Test case</th>
                  <th>Language</th>
                  <th>Topic</th>
                  <th>Retrieval</th>
                  <th>Answer</th>
                  <th>Citation</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((row) => (
                  <tr key={`${row.language}-${row.topic}`}>
                    <td>{row.title}</td>
                    <td>{row.languageName}</td>
                    <td>{row.topic.replaceAll("_", " ")}</td>
                    <td>{row.retrievalCorrect ? "Correct" : "Incorrect"}</td>
                    <td>
                      {row.answerCorrect === null
                        ? "Not evaluated"
                        : row.answerCorrect
                          ? "Correct"
                          : "Incorrect"}
                    </td>
                    <td>
                      {row.citationCorrect === null
                        ? "Not evaluated"
                        : row.citationCorrect
                          ? "Correct"
                          : "Incorrect"}
                    </td>
                    <td>
                      <StatusPill status={overallStatus(row)} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section aria-label="Voice capability">
        <h3>Voice capability</h3>
        <p className="eval-note">
          The evaluation voice rows check configured Gnani language codes and
          whether a sample string uses the expected script. They do not upload
          microphone audio. English and Tamil text-to-speech are the only
          playback pairs marked verified in the project voice mapping.
        </p>
        <div className="eval-table-wrap">
          <table>
            <thead>
              <tr>
                <th>Language</th>
                <th>STT code</th>
                <th>STT status</th>
                <th>TTS voice</th>
                <th>TTS status</th>
              </tr>
            </thead>
            <tbody>
              {interfaceVoice.map((row) => (
                <tr key={row.language}>
                  <td>
                    {coverage.find((item) => item.code === row.language)?.name ??
                      row.language}
                  </td>
                  <td>{row.sttLanguageCode ?? "—"}</td>
                  <td>
                    {row.sttConfigured
                      ? "Configured. Audio not scored."
                      : "Unsupported"}
                  </td>
                  <td>{row.ttsVoice ?? "—"}</td>
                  <td>
                    {row.language === "en" || row.language === "ta"
                      ? "Audio verified"
                      : row.ttsConfigured
                        ? "Configured. Not yet audio-tested."
                        : "Unsupported"}
                  </td>
                </tr>
              ))}
              {unsupportedVoice.map((row) => (
                <tr key={row.language}>
                  <td>{row.language === "or" ? "Odia" : row.language === "ur" ? "Urdu" : row.language}</td>
                  <td>—</td>
                  <td>Unsupported</td>
                  <td>—</td>
                  <td>Unsupported</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section aria-label="Evaluation insights">
        <h3>Evaluation insights</h3>
        <div className="eval-insights">
          <article>
            <h4>Strengths in this report</h4>
            <ul>
              <li>
                Retrieval was correct on {summary.retrieval_correct} of{" "}
                {summary.cases} cases.
              </li>
              <li>
                Citations were correct on {summary.citations_correct} of{" "}
                {summary.citations_scored} scored answers.
              </li>
              <li>
                The requested answer language matched on{" "}
                {summary.answer_language_correct} of {summary.answers_scored}{" "}
                scored answers.
              </li>
            </ul>
          </article>
          <article>
            <h4>Limitations</h4>
            <ul>
              <li>
                {summary.answers_failed} answers were not scored because the
                model call failed.
              </li>
              <li>
                {factFailures.length} scored answers failed the fact check.
              </li>
              <li>
                Precision, recall, and context relevance are not calculated by
                this suite.
              </li>
              <li>
                Speech-to-text has no audio pass/fail rows in the saved report.
              </li>
            </ul>
          </article>
        </div>

        <h4>Fact-check failures</h4>
        {factFailures.length === 0 ? (
          <p className="eval-empty">No fact-check failures were stored.</p>
        ) : (
          <ul className="eval-fail-list">
            {factFailures.map((row) => (
              <li key={`${row.language}-${row.topic}`}>
                {row.languageName} · {row.title}
              </li>
            ))}
          </ul>
        )}

        <h4>Model calls that were not scored</h4>
        <p className="eval-note">
          {callFailures.length} rows recorded answer_error chat_request_failed.
        </p>
      </section>
    </div>
  );
}
