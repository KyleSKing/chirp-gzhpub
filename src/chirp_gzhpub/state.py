"""Append-only JSONL state log for publishes.

Each line is a JSON object: {post, media_id, title, timestamp, status, error?}.
File is created lazily on first write. Records are append-only — no rotation.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

BJT = timezone(timedelta(hours=8))
DEFAULT_STATE_DIR = Path("state")
DEFAULT_STATE_FILE = DEFAULT_STATE_DIR / "wechat_publishes.jsonl"


def now_iso() -> str:
    return datetime.now(BJT).isoformat(timespec="seconds")


def record(
    *,
    post: str,
    media_id: str | None,
    title: str,
    status: str,
    state_file: Path = DEFAULT_STATE_FILE,
    error: str | None = None,
) -> None:
    """Append one publish record to the JSONL log."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    entry: dict[str, Any] = {
        "post": post,
        "media_id": media_id,
        "title": title,
        "timestamp": now_iso(),
        "status": status,
    }
    if error:
        entry["error"] = error
    with state_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def last_publish_for(post: str, state_file: Path = DEFAULT_STATE_FILE) -> dict[str, Any] | None:
    """Return the most recent record for a given post path, or None if never published."""
    if not state_file.exists():
        return None
    last: dict[str, Any] | None = None
    with state_file.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if entry.get("post") == post:
                last = entry
    return last


def decide_publish(
    post: str,
    state_file: Path = DEFAULT_STATE_FILE,
    *,
    force: bool = False,
) -> tuple[bool, str]:
    """Decide whether to publish `post` given its history in `state_file`.

    Returns (should_publish, reason):
      - (True, "...")  — proceed with publish
      - (False, "...") — skip, do not publish

    Rules:
      - No prior record        → publish.
      - Last entry is "failed" → publish (allows retry by default).
      - Last entry is "drafted":
          - force=True  → publish (explicit republish).
          - force=False → skip, surface the prior media_id + timestamp.
      - Any other status       → publish (don't silently swallow unknowns).
    """
    last = last_publish_for(post, state_file)
    if last is None:
        return True, "no prior publish record"
    status = last.get("status")
    if status == "failed":
        return True, f"retrying previous failure: {last.get('error', '')}"
    if status == "drafted":
        if force:
            return True, "force republish (overriding prior draft)"
        return False, (
            f"already drafted at {last.get('timestamp')} "
            f"(media_id={last.get('media_id')}); use --force to republish"
        )
    return True, f"unknown prior status {status!r}, defaulting to publish"
