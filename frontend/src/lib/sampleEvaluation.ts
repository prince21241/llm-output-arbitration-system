import type { EvaluateResponse } from "./types";

/** Sample docket on the public welcome page. Not live evaluation output. */
export const SAMPLE_EVALUATION: EvaluateResponse = {
  question: "When was the first iPhone released?",
  answer: "The first iPhone was released in 2005.",
  claims: [
    {
      id: "C1",
      text: "The first iPhone was released in 2005.",
      type: "date",
      evidence: [
        {
          title: "iPhone",
          url: "https://en.wikipedia.org/wiki/IPhone",
          snippet:
            "The first-generation iPhone was announced by Apple on January 9, 2007.",
          source: "wikipedia",
          overlap: 0.41,
        },
      ],
    },
  ],
  judge_results: [
    {
      judge: "openai",
      claim_id: "C1",
      verdict: "incorrect",
      confidence: 0.93,
      reason: "Apple announced the iPhone in January 2007, not 2005.",
    },
    {
      judge: "claude",
      claim_id: "C1",
      verdict: "incorrect",
      confidence: 0.91,
      reason:
        "The first iPhone went on sale in June 2007. 2005 is two years early.",
    },
    {
      judge: "gemini",
      claim_id: "C1",
      verdict: "incorrect",
      confidence: 0.88,
      reason: "Public record places the original iPhone in 2007.",
    },
  ],
  claim_consensus: [
    {
      claim_id: "C1",
      supporting_votes: 0,
      incorrect_votes: 3,
      uncertain_votes: 0,
      average_confidence: 0.907,
      agreement_score: 1,
      disagreement_score: 0,
      support_probability: 0.08,
      verdict: "incorrect",
    },
  ],
  consensus: {
    agreement_score: 1,
    support_score: 0.08,
    disagreement_score: 0,
  },
  final_confidence: 0.12,
  verdict: "incorrect",
  scorer: "rule",
};
