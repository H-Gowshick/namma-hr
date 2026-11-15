import { useMemo, useState } from "react";

import type { EvidenceItem } from "../../lib/evidenceTypes";
import { highlightPassage } from "./highlightPassage";
import {
  IconChevronDown,
  IconChevronUp,
  IconExternalLink,
  IconFileText,
} from "../icons";
import { messageTextDirection } from "../../lib/messageDirection";
import { documentPageUrl } from "../../lib/parseEvidenceStream";

import "./EvidenceExplorer.css";

type EvidenceExplorerProps = {
  items: EvidenceItem[] | null | undefined;
  ready: boolean;
  highlightQuery?: string;
};

function pageLabel(page: number | string): string {
  if (typeof page === "number" && Number.isFinite(page)) {
    return `Page ${page}`;
  }

  const text = String(page).trim();
  if (!text || text.toLowerCase() === "unknown page") {
    return "Page unavailable";
  }

  if (/^\d+$/.test(text)) {
    return `Page ${text}`;
  }

  return text;
}

function EvidenceCard({
  item,
  expanded,
  onToggle,
  highlightQuery,
}: {
  item: EvidenceItem;
  expanded: boolean;
  onToggle: () => void;
  highlightQuery?: string;
}) {
  const pdfUrl = documentPageUrl(item.source, item.page);
  const direction = messageTextDirection(item.text);
  const highlighted = useMemo(
    () =>
      highlightPassage(item.text, [
        highlightQuery ?? "",
        item.matched_query ?? "",
        item.heading,
      ]),
    [highlightQuery, item.heading, item.matched_query, item.text],
  );

  const panelId = `evidence-panel-${item.id}`;
  const preview =
    item.text.length > 160 ? `${item.text.slice(0, 160).trim()}…` : item.text;

  return (
    <article
      className={`evidence-card${expanded ? " is-expanded" : ""}`}
      data-evidence-id={item.id}
    >
      <button
        type="button"
        className="evidence-card-header"
        onClick={onToggle}
        aria-expanded={expanded}
        aria-controls={panelId}
      >
        <span className="evidence-card-icon" aria-hidden="true">
          <IconFileText size={16} />
        </span>

        <span className="evidence-card-meta">
          <span className="evidence-card-title">{item.source}</span>
          <span className="evidence-card-sub">
            {pageLabel(item.page)}
            {item.heading ? ` · ${item.heading}` : ""}
            {typeof item.relevance_score === "number"
              ? ` · Relevance ${item.relevance_score.toFixed(2)}`
              : ""}
          </span>
        </span>

        <span className="evidence-card-chevron" aria-hidden="true">
          {expanded ? <IconChevronUp size={16} /> : <IconChevronDown size={16} />}
        </span>
      </button>

      {!expanded ? (
        <p className="evidence-card-preview" dir={direction}>
          {preview}
        </p>
      ) : null}

      <div
        id={panelId}
        className="evidence-card-panel"
        hidden={!expanded}
      >
        <blockquote className="evidence-passage" dir={direction} lang="en">
          {highlighted}
        </blockquote>

        <div className="evidence-card-actions">
          {pdfUrl ? (
            <a
              className="evidence-open-link"
              href={pdfUrl}
              target="_blank"
              rel="noreferrer"
            >
              <IconExternalLink size={14} />
              Open PDF at {pageLabel(item.page).toLowerCase()}
            </a>
          ) : (
            <span className="evidence-open-missing">
              Original PDF unavailable for inspection
            </span>
          )}
        </div>
      </div>
    </article>
  );
}

export default function EvidenceExplorer({
  items,
  ready,
  highlightQuery = "",
}: EvidenceExplorerProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(() => new Set());

  if (!ready) {
    return null;
  }

  const evidenceItems = items ?? [];
  const count = evidenceItems.length;

  function toggle(id: string) {
    setExpandedIds((previous) => {
      const next = new Set(previous);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  return (
    <section className="evidence-explorer" aria-label="Sources and evidence">
      <header className="evidence-explorer-header">
        <div className="evidence-explorer-heading">
          <span className="evidence-explorer-kicker">Sources &amp; Evidence</span>
          <h3>Policy passages that support this answer</h3>
        </div>
        <span className="evidence-count">
          {count === 0 ? "No sources" : `${count} source${count === 1 ? "" : "s"}`}
        </span>
      </header>

      {count === 0 ? (
        <p className="evidence-empty">
          No supporting policy passages were retrieved for this answer.
        </p>
      ) : (
        <div className="evidence-card-list">
          {evidenceItems.map((item) => (
            <EvidenceCard
              key={item.id}
              item={item}
              expanded={expandedIds.has(item.id)}
              onToggle={() => toggle(item.id)}
              highlightQuery={highlightQuery}
            />
          ))}
        </div>
      )}
    </section>
  );
}
