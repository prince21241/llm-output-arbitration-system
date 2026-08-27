"""Per-user docket store. Every query is scoped to a Clerk user id."""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from app.schemas.evaluation import EvaluateResponse

HISTORY_LIMIT = 25


@dataclass(frozen=True)
class SavedDocketRecord:
    id: str
    saved_at: str
    result: EvaluateResponse


class DocketStore(Protocol):
    def upsert(self, user_id: str, result: EvaluateResponse) -> SavedDocketRecord: ...

    def list_for_user(
        self,
        user_id: str,
        limit: int = HISTORY_LIMIT,
    ) -> list[SavedDocketRecord]: ...

    def get_for_user(self, user_id: str, docket_id: str) -> SavedDocketRecord | None: ...

    def delete_for_user(self, user_id: str, docket_id: str) -> bool: ...


def _require_user_id(user_id: str) -> str:
    cleaned = user_id.strip()
    if not cleaned:
        raise ValueError("user_id is required")
    return cleaned


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class SqliteDocketStore:
    """SQLite dockets isolated by user_id. Never returns another user's rows."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        if str(self._path) != ":memory:":
            self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS dockets (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    final_confidence REAL NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_dockets_user_updated
                    ON dockets (user_id, updated_at DESC);
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def upsert(self, user_id: str, result: EvaluateResponse) -> SavedDocketRecord:
        owner = _require_user_id(user_id)
        question = result.question.strip()
        answer = result.answer.strip()
        payload = json.dumps(
            result.model_dump(mode="json", exclude={"id", "saved_at"}),
            separators=(",", ":"),
        )
        stamp = _now()
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT id FROM dockets
                WHERE user_id = ? AND question = ? AND answer = ?
                LIMIT 1
                """,
                (owner, question, answer),
            ).fetchone()
            docket_id = str(row["id"]) if row else str(uuid.uuid4())
            if row:
                conn.execute(
                    """
                    UPDATE dockets
                    SET verdict = ?, final_confidence = ?, payload = ?, updated_at = ?
                    WHERE id = ? AND user_id = ?
                    """,
                    (
                        result.verdict,
                        result.final_confidence,
                        payload,
                        stamp,
                        docket_id,
                        owner,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO dockets (
                        id, user_id, question, answer, verdict, final_confidence,
                        payload, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        docket_id,
                        owner,
                        question,
                        answer,
                        result.verdict,
                        result.final_confidence,
                        payload,
                        stamp,
                        stamp,
                    ),
                )
            self._prune(conn, owner)
            conn.commit()
        saved = self.get_for_user(owner, docket_id)
        if saved is None:
            raise RuntimeError("Failed to persist docket for the signed-in user.")
        return saved

    def list_for_user(
        self,
        user_id: str,
        limit: int = HISTORY_LIMIT,
    ) -> list[SavedDocketRecord]:
        owner = _require_user_id(user_id)
        capped = max(1, min(limit, HISTORY_LIMIT))
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, updated_at, payload
                FROM dockets
                WHERE user_id = ?
                ORDER BY updated_at DESC, id DESC
                LIMIT ?
                """,
                (owner, capped),
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def get_for_user(self, user_id: str, docket_id: str) -> SavedDocketRecord | None:
        owner = _require_user_id(user_id)
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, updated_at, payload
                FROM dockets
                WHERE id = ? AND user_id = ?
                LIMIT 1
                """,
                (docket_id, owner),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def delete_for_user(self, user_id: str, docket_id: str) -> bool:
        owner = _require_user_id(user_id)
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM dockets WHERE id = ? AND user_id = ?",
                (docket_id, owner),
            )
            conn.commit()
            return cursor.rowcount > 0

    def _prune(self, conn: sqlite3.Connection, user_id: str) -> None:
        conn.execute(
            """
            DELETE FROM dockets
            WHERE user_id = ?
              AND id IN (
                SELECT id FROM dockets
                WHERE user_id = ?
                ORDER BY updated_at DESC, id DESC
                LIMIT -1 OFFSET ?
              )
            """,
            (user_id, user_id, HISTORY_LIMIT),
        )

    def _row_to_record(self, row: sqlite3.Row) -> SavedDocketRecord:
        payload = json.loads(row["payload"])
        result = EvaluateResponse.model_validate(payload)
        return SavedDocketRecord(
            id=str(row["id"]),
            saved_at=str(row["updated_at"]),
            result=result,
        )
