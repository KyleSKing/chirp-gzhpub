"""Tests for chirp_gzhpub.state."""
from __future__ import annotations

import json
from pathlib import Path

from chirp_gzhpub.state import decide_publish, last_publish_for, record


def _append(state_file: Path, entry: dict) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with state_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def test_no_state_file_means_publish(tmp_path: Path) -> None:
    state_file = tmp_path / "state.jsonl"
    should, reason = decide_publish("p.md", state_file)
    assert should is True
    assert "no prior" in reason


def test_empty_state_file_means_publish(tmp_path: Path) -> None:
    state_file = tmp_path / "state.jsonl"
    state_file.write_text("", encoding="utf-8")
    should, _ = decide_publish("p.md", state_file)
    assert should is True


def test_prior_failure_means_publish(tmp_path: Path) -> None:
    state_file = tmp_path / "state.jsonl"
    _append(state_file, {
        "post": "p.md", "media_id": None, "title": "T",
        "timestamp": "2026-08-09T10:00:00+08:00", "status": "failed",
        "error": "timeout",
    })
    should, reason = decide_publish("p.md", state_file)
    assert should is True
    assert "retrying" in reason
    assert "timeout" in reason


def test_prior_draft_skips_without_force(tmp_path: Path) -> None:
    state_file = tmp_path / "state.jsonl"
    _append(state_file, {
        "post": "p.md", "media_id": "draft_abc", "title": "T",
        "timestamp": "2026-08-09T10:00:00+08:00", "status": "drafted",
    })
    should, reason = decide_publish("p.md", state_file)
    assert should is False
    assert "draft_abc" in reason
    assert "--force" in reason


def test_prior_draft_publishes_with_force(tmp_path: Path) -> None:
    state_file = tmp_path / "state.jsonl"
    _append(state_file, {
        "post": "p.md", "media_id": "draft_abc", "title": "T",
        "timestamp": "2026-08-09T10:00:00+08:00", "status": "drafted",
    })
    should, reason = decide_publish("p.md", state_file, force=True)
    assert should is True
    assert "force" in reason.lower()


def test_other_post_history_does_not_affect_decision(tmp_path: Path) -> None:
    """Entries for other posts must not influence this post's decision."""
    state_file = tmp_path / "state.jsonl"
    _append(state_file, {
        "post": "other.md", "media_id": "draft_x", "title": "Other",
        "timestamp": "2026-08-09T10:00:00+08:00", "status": "drafted",
    })
    should, _ = decide_publish("p.md", state_file)
    assert should is True


def test_last_record_wins(tmp_path: Path) -> None:
    """Most recent entry for the same post is the one consulted (not the first)."""
    state_file = tmp_path / "state.jsonl"
    _append(state_file, {
        "post": "p.md", "media_id": None, "title": "T",
        "timestamp": "2026-08-09T09:00:00+08:00", "status": "failed", "error": "first",
    })
    _append(state_file, {
        "post": "p.md", "media_id": "draft_v2", "title": "T",
        "timestamp": "2026-08-09T10:00:00+08:00", "status": "drafted",
    })
    should, reason = decide_publish("p.md", state_file)
    assert should is False  # latest entry is drafted
    assert "draft_v2" in reason


def test_unknown_status_defaults_to_publish(tmp_path: Path) -> None:
    state_file = tmp_path / "state.jsonl"
    _append(state_file, {
        "post": "p.md", "media_id": None, "title": "T",
        "timestamp": "2026-08-09T10:00:00+08:00", "status": "frobnicated",
    })
    should, reason = decide_publish("p.md", state_file)
    assert should is True
    assert "unknown" in reason


def test_record_and_last_publish_round_trip(tmp_path: Path) -> None:
    """Sanity check that record() + last_publish_for() work as expected."""
    state_file = tmp_path / "state.jsonl"
    record(post="p.md", media_id="draft_1", title="T", status="drafted", state_file=state_file)
    record(post="p.md", media_id=None, title="T", status="failed", state_file=state_file, error="x")
    last = last_publish_for("p.md", state_file)
    assert last is not None
    assert last["status"] == "failed"
    assert last["error"] == "x"
