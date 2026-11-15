import { useEffect, useMemo, useState } from "react";

import type { ReactNode } from "react";

import {
  IconBaby,
  IconCalendar,
  IconExternalLink,
  IconFileText,
  IconHeartPulse,
  IconHome,
  IconSearch,
  IconSparkles,
} from "../icons";
import { apiUrl } from "../../lib/apiBase";
import { messageTextDirection } from "../../lib/messageDirection";
import { documentPageUrl } from "../../lib/parseEvidenceStream";
import {
  POLICY_CATEGORIES,
  type PolicyCategory,
  type PolicyCategoryId,
} from "../../lib/policyCatalog";

import "./PolicyLibrary.css";

type PolicyPassage = {
  text: string;
  source: string;
  page: number | string;
  heading: string;
};

type PassageState = {
  status: "loading" | "ready" | "error";
  passages: PolicyPassage[];
};

type PolicyLibraryProps = {
  askingDisabled: boolean;
  onAsk: (prompt: string) => void;
};

const ICONS: Record<PolicyCategoryId, ReactNode> = {
  "casual-leave": <IconCalendar size={18} />,
  "sick-leave": <IconHeartPulse size={18} />,
  "earned-leave": <IconCalendar size={18} />,
  "maternity-leave": <IconBaby size={18} />,
  "paternity-leave": <IconBaby size={18} />,
  "work-from-home": <IconHome size={18} />,
};

function pageLabel(page: number | string): string {
  if (typeof page === "number" && Number.isFinite(page)) {
    return `Page ${page}`;
  }

  const text = String(page).trim();
  if (!text || text.toLowerCase() === "unknown page") {
    return "Page unavailable";
  }

  return /^\d+$/.test(text) ? `Page ${text}` : text;
}

function matchesCategory(text: string, category: PolicyCategory): boolean {
  const lowered = text.toLowerCase();
  return category.matchTerms.some((term) => lowered.includes(term));
}

async function loadPassages(category: PolicyCategory): Promise<PolicyPassage[]> {
  const response = await fetch(apiUrl("/retrieve"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: category.query,
      top_k: 4,
    }),
  });

  if (!response.ok) {
    throw new Error(`Retrieval failed (${response.status})`);
  }

  const data = (await response.json()) as {
    results?: Array<{
      text?: string;
      source?: string;
      page?: number | string;
      heading?: string;
    }>;
  };

  const seen = new Set<string>();
  const passages: PolicyPassage[] = [];

  for (const item of data.results ?? []) {
    const text = (item.text ?? "").trim();
    if (!text || !matchesCategory(text, category)) {
      continue;
    }

    const source = (item.source ?? "Unknown source").split(/[\\/]/).pop() ?? "Unknown source";
    const page = item.page ?? "Unknown page";
    const key = `${source}|${page}|${text.slice(0, 160)}`;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);

    passages.push({
      text,
      source,
      page,
      heading: (item.heading ?? "General").trim() || "General",
    });
  }

  return passages;
}

export default function PolicyLibrary({
  askingDisabled,
  onAsk,
}: PolicyLibraryProps) {
  const [query, setQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<PolicyCategoryId | "all">("all");
  const [openId, setOpenId] = useState<PolicyCategoryId | null>(null);
  const [passages, setPassages] = useState<Record<string, PassageState>>({});

  useEffect(() => {
    let cancelled = false;

    async function loadAll() {
      setPassages(
        Object.fromEntries(
          POLICY_CATEGORIES.map((category) => [
            category.id,
            { status: "loading", passages: [] },
          ]),
        ),
      );

      await Promise.all(
        POLICY_CATEGORIES.map(async (category) => {
          try {
            const items = await loadPassages(category);
            if (cancelled) {
              return;
            }
            setPassages((previous) => ({
              ...previous,
              [category.id]: { status: "ready", passages: items },
            }));
          } catch {
            if (cancelled) {
              return;
            }
            setPassages((previous) => ({
              ...previous,
              [category.id]: { status: "error", passages: [] },
            }));
          }
        }),
      );
    }

    void loadAll();

    return () => {
      cancelled = true;
    };
  }, []);

  const visibleCategories = useMemo(() => {
    const needle = query.trim().toLowerCase();

    return POLICY_CATEGORIES.filter((category) => {
      if (activeFilter !== "all" && category.id !== activeFilter) {
        return false;
      }

      if (!needle) {
        return true;
      }

      const state = passages[category.id];
      const inPassages = (state?.passages ?? []).some((passage) =>
        passage.text.toLowerCase().includes(needle),
      );

      return (
        category.title.toLowerCase().includes(needle) ||
        category.summary.toLowerCase().includes(needle) ||
        inPassages
      );
    });
  }, [activeFilter, passages, query]);

  return (
    <section className="policy-library" aria-label="HR Policy Library">
      <header className="policy-library-hero">
        <div>
          <p className="policy-library-kicker">Policy library</p>
          <h2>Explore HR policies</h2>
          <p>
            Open a topic to read passages retrieved from your uploaded handbook.
            Card descriptions are navigation only. Rules, days, and eligibility
            appear solely in the verified document text.
          </p>
        </div>
      </header>

      <div className="policy-library-toolbar">
        <label className="policy-search">
          <IconSearch size={16} />
          <input
            type="search"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
            }}
            placeholder="Search policies or retrieved text"
            aria-label="Search policies"
          />
        </label>

        <div className="policy-filters" role="tablist" aria-label="Policy categories">
          <button
            type="button"
            className={`policy-filter${activeFilter === "all" ? " is-active" : ""}`}
            onClick={() => {
              setActiveFilter("all");
            }}
          >
            All
          </button>
          {POLICY_CATEGORIES.map((category) => (
            <button
              key={category.id}
              type="button"
              className={`policy-filter${activeFilter === category.id ? " is-active" : ""}`}
              onClick={() => {
                setActiveFilter(category.id);
              }}
            >
              {category.title}
            </button>
          ))}
        </div>
      </div>

      {visibleCategories.length === 0 ? (
        <div className="policy-empty" role="status">
          <IconFileText size={18} />
          <div>
            <strong>No matching policy</strong>
            <p>Nothing in the library matches that search. Try another topic name.</p>
          </div>
        </div>
      ) : (
        <div className="policy-grid">
          {visibleCategories.map((category) => {
            const state = passages[category.id];
            const open = openId === category.id;
            const panelId = `policy-panel-${category.id}`;

            return (
              <article
                key={category.id}
                className={`policy-card${open ? " is-open" : ""}`}
              >
                <button
                  type="button"
                  className="policy-card-toggle"
                  aria-expanded={open}
                  aria-controls={panelId}
                  onClick={() => {
                    setOpenId(open ? null : category.id);
                  }}
                >
                  <span className="policy-card-icon" aria-hidden="true">
                    {ICONS[category.id]}
                  </span>
                  <span className="policy-card-copy">
                    <strong>{category.title}</strong>
                    <span>{category.summary}</span>
                  </span>
                </button>

                {open ? (
                  <div id={panelId} className="policy-card-detail">
                    <p className="policy-verified-label">Verified document passages</p>

                    {state?.status === "loading" ? (
                      <p className="policy-detail-status">Retrieving handbook passages…</p>
                    ) : null}

                    {state?.status === "error" ? (
                      <p className="policy-detail-status">
                        The policy documents could not be retrieved right now.
                      </p>
                    ) : null}

                    {state?.status === "ready" && state.passages.length === 0 ? (
                      <div className="policy-empty policy-empty--inline" role="status">
                        <div>
                          <strong>No supporting passage found</strong>
                          <p>
                            The uploaded HR policy documents did not return a passage
                            for {category.title}.
                          </p>
                        </div>
                      </div>
                    ) : null}

                    {state?.status === "ready"
                      ? state.passages.map((passage) => {
                          const direction = messageTextDirection(passage.text);
                          const href = documentPageUrl(passage.source, passage.page);

                          return (
                            <figure
                              key={`${passage.source}-${passage.page}-${passage.text.slice(0, 40)}`}
                              className="policy-passage"
                            >
                              <figcaption>
                                <IconFileText size={14} />
                                <span>
                                  {passage.source} · {pageLabel(passage.page)}
                                  {passage.heading ? ` · ${passage.heading}` : ""}
                                </span>
                              </figcaption>
                              <blockquote dir={direction} lang="en">
                                {passage.text}
                              </blockquote>
                              {href ? (
                                <a href={href} target="_blank" rel="noreferrer">
                                  <IconExternalLink size={13} />
                                  Open PDF
                                </a>
                              ) : null}
                            </figure>
                          );
                        })
                      : null}

                    <button
                      type="button"
                      className="policy-ask"
                      disabled={askingDisabled}
                      onClick={() => {
                        onAsk(category.askPrompt);
                      }}
                    >
                      <IconSparkles size={15} />
                      Ask AI about this policy
                    </button>
                  </div>
                ) : null}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
