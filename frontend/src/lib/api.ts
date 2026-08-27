import type {
  DocketListResponse,
  EvaluateResponse,
  HealthResponse,
  SavedDocket,
} from "./types";

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function authHeaders(token?: string | null): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

export async function evaluateAnswer(
  question: string,
  answer: string,
  token?: string | null,
): Promise<EvaluateResponse> {
  const response = await fetch("/api/v1/evaluate", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ question, answer }),
  });

  if (!response.ok) {
    throw new ApiError(await readApiError(response), response.status);
  }

  return (await response.json()) as EvaluateResponse;
}

export async function listDockets(token?: string | null): Promise<SavedDocket[]> {
  const response = await fetch("/api/v1/dockets", {
    headers: authHeaders(token),
  });
  if (!response.ok) {
    throw new ApiError(await readApiError(response), response.status);
  }
  const body = (await response.json()) as DocketListResponse;
  return Array.isArray(body.dockets) ? body.dockets : [];
}

export async function deleteDocket(
  docketId: string,
  token?: string | null,
): Promise<void> {
  const response = await fetch(`/api/v1/dockets/${encodeURIComponent(docketId)}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
  if (!response.ok) {
    throw new ApiError(await readApiError(response), response.status);
  }
}

export async function fetchHealth(): Promise<HealthResponse | null> {
  try {
    const response = await fetch("/health");
    if (!response.ok) return null;
    return (await response.json()) as HealthResponse;
  } catch {
    return null;
  }
}

async function readApiError(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (body && typeof body === "object" && "detail" in body) {
      const detail = (body as { detail: unknown }).detail;
      if (typeof detail === "string" && detail.trim()) return detail;
      if (Array.isArray(detail)) {
        const messages = detail
          .map((item) =>
            item && typeof item === "object" && "msg" in item
              ? String((item as { msg: unknown }).msg)
              : "",
          )
          .filter(Boolean);
        if (messages.length) return messages.join(". ");
      }
    }
  } catch {
    /* use status fallback */
  }

  if (response.status === 401) return "Sign in to evaluate answers.";
  if (response.status === 404) return "Docket not found.";
  if (response.status === 422) return "Check the question and answer fields.";
  if (response.status >= 500) return "The evaluator failed. Try again.";
  return "Evaluation did not complete. Try again.";
}
