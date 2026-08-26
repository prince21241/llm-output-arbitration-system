# LLM Output Arbitration System

Backend for evaluating AI-generated answers. The service accepts a user question plus a model response, extracts factual claims, retrieves Wikipedia evidence, sends those claims to judge models, and returns a structured **preliminary** confidence score from either a rule formula or a trained model.

This repository currently implements **Phases 1-3 plus a first ML scorer**: FastAPI pipeline, optional OpenAI / Claude / Gemini judges, Wikipedia evidence, a seed labeled set, and `MLConfidenceModel`. There is no database yet. Provider API keys are still optional.

## Purpose

Language models often state facts with more certainty than the evidence supports. This project treats that as an arbitration problem:

1. Break an answer into checkable claims.
2. Retrieve short sources for each claim.
3. Collect independent verdicts from several judges.
4. Combine those verdicts (and evidence overlap) into a preliminary confidence score.

## Current architecture

```text
Question + Answer
        │
        ▼
 ClaimExtractor          (heuristic sentence split + type tags)
        │
        ▼
 EvidenceRetriever       (Wikipedia search snippets)
        │
        ▼
   JudgeRouter           (asyncio.gather over BaseJudge implementations)
        │
        ▼
 ConsensusEngine         (RuleBasedScorer or MLConfidenceModel)
        │
        ▼
    Evaluator            (overall weighted score + verdict)
        │
        ▼
 POST /api/v1/evaluate
```

Key design choices:

- FastAPI routes do not contain pipeline logic.
- Judges implement `BaseJudge.evaluate_claim`. `build_judges` registers `OpenAIJudge`, `ClaudeJudge`, and `GeminiJudge` when their keys are present. Otherwise it uses `MockJudgeA` and `MockJudgeB`.
- Evidence is Wikipedia-only in this phase. Failures return an empty list so judging still runs.
- Scoring implements `support_probability`. `MLConfidenceModel` loads `app/ml/artifacts/confidence_model.joblib` when `USE_ML_SCORER=true`. Otherwise `RuleBasedScorer` is used. Retrain with `python -m app.ml.train` from `backend/`.
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

Copy environment placeholders if you want a local `.env` file. API keys are optional. Empty keys keep the mock judges.

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Set any combination of `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and `GEMINI_API_KEY`. Cheap defaults are `gpt-4o-mini`, `claude-haiku-4-5`, and `gemini-2.5-flash`. Override with `OPENAI_MODEL`, `ANTHROPIC_MODEL`, and `GEMINI_MODEL`. `USE_MOCK_JUDGES=true` forces mocks even when keys are set.

`GET /health` reports `mode` (`live` or `mock`) and the registered `judges` list. It never returns API keys.

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

Tests use in-process mock judges and mocked HTTP. They do not need internet access or API keys.

Retrain the confidence model from `backend/`:

```bash
python -m app.ml.train
```

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
  "service": "llm-output-arbitrator",
  "mode": "mock",
  "judges": ["mock_judge_a", "mock_judge_b"]
}
```

## Example response

Exact floats depend on the scoring rule, but the shape is stable. With no API keys, judge names are the mocks:

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
- Evidence is Wikipedia search snippets, not a full citation graph. Paid search is still later.
- Live judges can read those snippets when keys are set. With mock judges, evidence is shown but does not change the hard-coded votes.
- The ML scorer is trained on synthetic vote patterns plus a small labeled seed set. Retrain after live judges produce real labels.
- No authentication, persistence, caching, or rate limits.
- Empty provider keys fall back to deterministic mocks with a tiny knowledge table.

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
Evidence retrieval and source verification (Wikipedia, current)

Phase 4
Grok / DeepSeek / Kimi integrations

Phase 5
Evaluation dataset creation (seed file started)

Phase 6
ML confidence model (logistic + histogram gradient boosting, current)

Phase 7
Probability calibration and benchmark evaluation (sigmoid calibration included)

Phase 8
Frontend polish, auth, and persistence

Phase 9
PostgreSQL, caching, rate limits, cost tracking

Phase 10
Docker and production deployment
```
