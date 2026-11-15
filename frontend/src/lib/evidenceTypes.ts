export type EvidenceItem = {
  id: string;
  source: string;
  page: number | string;
  heading: string;
  text: string;
  matched_query?: string;
  relevance_score?: number;
};

export type EvidencePayload = {
  version: number;
  items: EvidenceItem[];
};
