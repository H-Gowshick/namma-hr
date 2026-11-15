export type PolicyCategoryId =
  | "casual-leave"
  | "sick-leave"
  | "earned-leave"
  | "maternity-leave"
  | "paternity-leave"
  | "work-from-home";

export type PolicyCategory = {
  id: PolicyCategoryId;
  title: string;
  /** Navigation copy only. Policy rules come from retrieval, not this text. */
  summary: string;
  /** Sent to the existing /retrieve endpoint. */
  query: string;
  /** Passage must contain one of these phrases before it is shown. */
  matchTerms: string[];
  /** Question sent through the existing /chat flow. */
  askPrompt: string;
};

export const POLICY_CATEGORIES: PolicyCategory[] = [
  {
    id: "casual-leave",
    title: "Casual Leave",
    summary:
      "Browse handbook passages retrieved for casual leave. Entitlements appear only in the source text below.",
    query: "casual leave entitlement",
    matchTerms: ["casual leave"],
    askPrompt: "What does the HR policy say about casual leave?",
  },
  {
    id: "sick-leave",
    title: "Sick Leave",
    summary:
      "Browse handbook passages retrieved for sick or medical leave. Rules appear only in the source text below.",
    query: "sick leave medical leave",
    matchTerms: ["sick leave", "medical leave"],
    askPrompt: "What does the HR policy say about sick leave?",
  },
  {
    id: "earned-leave",
    title: "Earned Leave",
    summary:
      "Browse handbook passages retrieved for earned or privilege leave. Rules appear only in the source text below.",
    query: "earned leave privilege leave",
    matchTerms: ["earned leave", "privilege leave", "privileged leave"],
    askPrompt: "What does the HR policy say about earned leave?",
  },
  {
    id: "maternity-leave",
    title: "Maternity Leave",
    summary:
      "Browse handbook passages retrieved for maternity leave. Rules appear only in the source text below.",
    query: "maternity leave",
    matchTerms: ["maternity"],
    askPrompt: "What does the HR policy say about maternity leave?",
  },
  {
    id: "paternity-leave",
    title: "Paternity Leave",
    summary:
      "Browse handbook passages retrieved for paternity leave. Rules appear only in the source text below.",
    query: "paternity leave",
    matchTerms: ["paternity"],
    askPrompt: "What does the HR policy say about paternity leave?",
  },
  {
    id: "work-from-home",
    title: "Work From Home",
    summary:
      "Browse handbook passages retrieved for work from home. Rules appear only in the source text below.",
    query: "work from home policy",
    matchTerms: ["work from home", "work-from-home"],
    askPrompt: "What does the HR policy say about work from home?",
  },
];
