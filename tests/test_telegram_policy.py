from __future__ import annotations

import json
from datetime import datetime, timezone

import scripts.send_telegram_alerts as telegram


def _item(item_id: str, *, sent: bool = False, closing: bool = False) -> dict:
    return {
        "id": item_id,
        "title": f"Cargo {item_id}",
        "institution": "Servicio Publico",
        "match_level": "Alta",
        "match_score": 90,
        "is_new_since_last_run": not closing,
        "urgency": "proximo" if closing else "normal",
        "economic_viability": "cumple_bueno",
        "source_url": "https://example.test",
        "region": "Maule",
        "commune": "Talca",
    }


def test_automatic_policy_keeps_daily_limit() -> None:
    now = datetime(2026, 6, 12, 15, tzinfo=timezone.utc)
    state = {"sent_opportunity_ids": [], "last_auto_sent_at": now.isoformat()}
    would_send, reason, included = telegram.evaluate_automatic_policy([_item("new")], state, now=now)
    assert would_send is False
    assert included == []
    assert "hoy" in reason


def test_automatic_policy_excludes_already_sent_ids() -> None:
    state = {"sent_opportunity_ids": ["already"], "last_auto_sent_at": None}
    would_send, reason, included = telegram.evaluate_automatic_policy([_item("already")], state)
    assert would_send is False
    assert included == []
    assert "no notificadas" in reason


def test_automatic_state_updates_only_after_success(monkeypatch, tmp_path) -> None:
    state_path = tmp_path / "telegram_state.json"
    state_path.write_text('{"sent_opportunity_ids": [], "last_auto_sent_at": null}\n', encoding="utf-8")
    monkeypatch.setenv("TELEGRAM_AUTO_ENABLED", "true")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat")
    monkeypatch.setattr(
        telegram,
        "load_public_data",
        lambda: ([_item("new")], {}, {"finished_at": "2026-06-12T15:00:00+00:00"}),
    )
    calls = []
    monkeypatch.setattr(telegram, "_send_message", lambda message, token, chat_id: calls.append(message) or 0)

    assert telegram._run_automatic(send=True, state_path=state_path) == 0
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["last_mode"] == "automatic"
    assert state["sent_opportunity_ids"] == ["new"]
    assert state["last_alert_batch_id"]
    assert calls


def test_automatic_state_not_updated_after_telegram_error(monkeypatch, tmp_path) -> None:
    state_path = tmp_path / "telegram_state.json"
    original = '{"sent_opportunity_ids": [], "last_auto_sent_at": null}\n'
    state_path.write_text(original, encoding="utf-8")
    monkeypatch.setenv("TELEGRAM_AUTO_ENABLED", "true")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat")
    monkeypatch.setattr(
        telegram,
        "load_public_data",
        lambda: ([_item("new")], {}, {"finished_at": "2026-06-12T15:00:00+00:00"}),
    )
    monkeypatch.setattr(telegram, "_send_message", lambda message, token, chat_id: 1)

    assert telegram._run_automatic(send=True, state_path=state_path) == 1
    assert state_path.read_text(encoding="utf-8") == original


def test_telegram_state_atomic_write_success(tmp_path) -> None:
    state_path = tmp_path / "telegram_state.json"
    telegram._write_state(state_path, {"sent_opportunity_ids": ["one"]})
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state == {"sent_opportunity_ids": ["one"]}


def test_telegram_state_write_failure_preserves_previous(monkeypatch, tmp_path) -> None:
    state_path = tmp_path / "telegram_state.json"
    original = '{"sent_opportunity_ids": ["old"]}\n'
    state_path.write_text(original, encoding="utf-8")

    def failing_atomic(path, state):
        raise OSError("cannot write temp")

    monkeypatch.setattr(telegram, "atomic_write_json", failing_atomic)
    try:
        telegram._write_state(state_path, {"sent_opportunity_ids": ["new"]})
    except OSError:
        pass
    assert state_path.read_text(encoding="utf-8") == original
