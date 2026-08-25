export type Verdict = "supported" | "incorrect" | "uncertain";
export type ClaimType = "factual" | "numerical" | "date" | "unknown";

export type Claim = {
  id: string;
  text: string;
  type: ClaimType;
};

export type JudgeResult = {
  judge: string;
  claim_id: string;
  verdict: Verdict;
  confidence: number;
  reason: string;
};

export type ClaimConsensus = {
  claim_id: string;
  supporting_votes: number;
  incorrect_votes: number;
  uncertain_votes: number;
  average_confidence: number;
  agreement_score: number;
  disagreement_score: number;
  support_probability: number;
  verdict: Verdict;
};

export type OverallConsensus = {
  agreement_score: number;
  support_score: number;
  disagreement_score: number;
};

export type EvaluateResponse = {
  question: string;
  answer: string;
  claims: Claim[];
  judge_results: JudgeResult[];
  claim_consensus: ClaimConsensus[];
  consensus: OverallConsensus;
  final_confidence: number;
  verdict: Verdict;
};

export type HealthResponse = {
  status: string;
  service: string;
};
