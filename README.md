# LLM Output Arbitration System

Phase 1 backend for evaluating AI-generated answers. The service accepts a user question plus a model response, extracts factual claims, sends those claims to multiple judge models, compares their evaluations, and returns a structured **preliminary** confidence score.

This repository currently implements **Phase 1**: a FastAPI evaluation pipeline with mock judges, plus a React workspace that calls it. There is no database, live web search, or paid model integration yet.

## Purpose

Language models often state facts with more certainty than the evidence supports. This project treats that as an arbitration problem:

1. Break an answer into checkable claims.
2. Collect independent verdicts from several judges.
3. Combine those verdicts into an agreement profile and a preliminary confidence score.
4. Keep every stage replaceable so later phases can add real models, evidence retrieval, and a trained confidence estimator.

## Current Phase 1 architecture

```text
Question + Answer
        │
        ▼
 ClaimExtractor          (heuristic sentence split + type tags)
        │
        ▼
   JudgeRouter           (asyncio.gather over BaseJudge implementations)
        │
        ▼
 ConsensusEngine         (rule-based signed-confidence scoring)
        │
        ▼
    Evaluator            (overall weighted score + verdict)
        │
        ▼
 POST /api/v1/evaluate
```

Key design choices:

- FastAPI routes do not contain pipeline logic.
- Judges implement `BaseJudge.evaluate_claim`. Phase 1 uses `MockJudgeA` and `MockJudgeB`. Later providers (`OpenAIJudge`, `ClaudeJudge`, `GeminiJudge`, `GrokJudge`, `DeepSeekJudge`, `KimiJudge`) can be registered on `JudgeRouter` without rewriting the evaluator.
- Scoring lives in `RuleBasedScorer`. A future `MLConfidenceModel.predict(features)` can replace it through the same `support_probability` contract.
- Verdict thresholds (`0.75` supported / `0.35` incorrect) are configuration, not scattered constants.

## Installation

Requires **Python 3.12+**.

### Create a virtual environment

**Windows (PowerShell)**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

Copy environment placeholders if you want a local `.env` file. API keys are **not** required for Phase 1.

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

## Start FastAPI

From the `backend/` directory, with the virtual environment active:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Run tests

From `backend/`:

```bash
pytest
```

Tests use in-process mock judges only. They do not need internet access or API keys.

## Example API request

```http
POST /api/v1/evaluate
Content-Type: application/json
```

```json
{
  "question": "When was the first iPhone released?",
  "answer": "The first iPhone was released in 2005."
}
```

cURL:

```bash
curl -s http://127.0.0.1:8000/api/v1/evaluate ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"When was the first iPhone released?\",\"answer\":\"The first iPhone was released in 2005.\"}"
```

Health check:

```bash
curl -s http://127.0.0.1:8000/health
```

```json
{
  "status": "ok",
  "service": "llm-output-arbitrator"
}
```

## Example response

Exact floats depend on the scoring rule, but the shape is stable:

```json
{
  "question": "When was the first iPhone released?",
  "answer": "The first iPhone was released in 2005.",
  "claims": [
    {
      "id": "claim_1",
      "text": "The first iPhone was released in 2005.",
      "type": "date"
    }
  ],
  "judge_results": [
    {
      "judge": "mock_judge_a",
      "claim_id": "claim_1",
      "verdict": "incorrect",
      "confidence": 0.95,
      "reason": "The first iPhone was released in 2007, not 2005."
    },
    {
      "judge": "mock_judge_b",
      "claim_id": "claim_1",
      "verdict": "incorrect",
      "confidence": 0.92,
      "reason": "The date conflicts with known information: the first iPhone launched in 2007."
    }
  ],
  "claim_consensus": [
    {
      "claim_id": "claim_1",
      "supporting_votes": 0,
      "incorrect_votes": 2,
      "uncertain_votes": 0,
      "average_confidence": 0.935,
      "agreement_score": 1.0,
      "disagreement_score": 0.0,
      "support_probability": 0.0325,
      "verdict": "incorrect"
    }
  ],
  "consensus": {
    "agreement_score": 1.0,
    "support_score": 0.0325,
    "disagreement_score": 0.0
  },
  "final_confidence": 0.0325,
  "verdict": "incorrect"
}
```

`final_confidence` is a **preliminary** score. It is a normalized signed-confidence average, not a scientifically calibrated probability.

## Current limitations

- Claim extraction is rule-based (sentence splitting + regex), not an LLM.
- Judges are deterministic mocks with a tiny knowledge table.
- There is no web search, citation check, or source retrieval.
- Consensus scoring is a transparent formula, not a trained model.
- No authentication, persistence, caching, or rate limits.
- Provider API keys are placeholders and unused.

## Frontend

From `frontend/`, with the API already running on port 8000:

```bash
npm install
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). The workspace posts to `POST /api/v1/evaluate`.

## Planned roadmap

```text
Phase 1
Core evaluation pipeline + mock judges

Phase 2
Real OpenAI / Claude / Gemini integrations

Phase 3
Evidence retrieval and source verification

Phase 4
Grok / DeepSeek / Kimi integrations

Phase 5
Evaluation dataset creation

Phase 6
ML confidence model using Logistic Regression and XGBoost/LightGBM

Phase 7
Probability calibration and benchmark evaluation

Phase 8
Frontend polish, auth, and persistence

Phase 9
PostgreSQL, caching, rate limits, cost tracking

Phase 10
Docker and production deployment
```
