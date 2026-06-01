"""Send a validated Telegram preview only after explicit operator confirmation."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "output" / "telegram" / "telegram-preview.txt"


def _masked_chat_id(chat_id: str) -> str:
    return f"{chat_id[:2]}***{chat_id[-2:]}" if len(chat_id) > 4 else "****"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--send", action="store_true", help="Confirmar envío real por Telegram.")
    args = parser.parse_args()

    if not args.send:
        print("Envío bloqueado: falta confirmación explícita --send.")
        return 0

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Envío bloqueado: configura TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID.")
        return 0
    if not PREVIEW.exists():
        print("ERROR: primero genera output/telegram/telegram-preview.txt.", file=sys.stderr)
        return 1

    message = PREVIEW.read_text(encoding="utf-8")
    data = urlencode({"chat_id": chat_id, "text": message, "disable_web_page_preview": "true"}).encode("utf-8")
    request = Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data, method="POST")
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        print(f"ERROR: Telegram no confirmó el envío para chat {_masked_chat_id(chat_id)}: {error}", file=sys.stderr)
        return 1
    if payload.get("ok") is not True:
        print(f"ERROR: Telegram rechazó el envío para chat {_masked_chat_id(chat_id)}.", file=sys.stderr)
        return 1
    print(f"Telegram enviado correctamente al chat {_masked_chat_id(chat_id)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
