# Agent instructions

This repo is a FastAPI evaluation pipeline plus a React workspace that calls `POST /api/v1/evaluate`.

## Frontend

Before generating or changing UI, read `DESIGN.md` and apply:

- `.agents/skills/design-taste-frontend/SKILL.md` for anti-slop visual rules (no Inter default, no purple glow, no em-dash, dark theme only, Phosphor icons, Motion for UI motion).
- `.agents/skills/web-design-guidelines/SKILL.md` for interaction and accessibility (focus, keyboard, forms, loading, reduced motion).

This product is a forensic workspace, not a marketing landing page. Taste Skill landing-page blocks (bento, logo wall, manifesto hero) do not apply to the evaluate docket. Keep anti-slop rules. Keep density appropriate for claims, votes, and scores.

Stack: Vite, React, TypeScript, Tailwind v4, Motion (`motion/react`), `@phosphor-icons/react`, Outfit + IBM Plex Mono.

## Backend

Do not put pipeline logic in FastAPI routes. Swap judges on `JudgeRouter` via `build_judges`. Scoring stays behind `RuleBasedScorer` / `MLConfidenceModel` / `support_probability`. Evidence stays behind `EvidenceRetriever`.

Live judges (`OpenAIJudge`, `ClaudeJudge`, `GeminiJudge`) register when their API keys are set. Tests and key-less local runs use `MockJudgeA` / `MockJudgeB`. Do not call paid APIs from tests. Wikipedia evidence is free; tests must mock it.

Local API: `http://127.0.0.1:8000`. Vite proxies `/api` and `/health` to that origin.

## Copy

No em-dash (`—`) or en-dash (`–`) in user-visible strings. Use a hyphen.
