"""Minimal Telegram bot client: send text/video, read replies from your chat."""
import requests

from .core import env

API = "https://api.telegram.org/bot{}/{}"


def _call(method, **kw):
    try:
        r = requests.post(API.format(env("TELEGRAM_BOT_TOKEN"), method), timeout=120, **kw)
    except requests.RequestException as e:
        raise RuntimeError(f"Telegram {method}: network error {type(e).__name__}") from None
    if r.status_code != 200:  # never include the URL: it contains the bot token
        hint = " (check TELEGRAM_BOT_TOKEN)" if r.status_code in (401, 404) else ""
        raise RuntimeError(f"Telegram {method} failed: HTTP {r.status_code} {r.text[:200]}{hint}")
    return r.json()["result"]


def send(text):
    for i in range(0, len(text), 3900):  # Telegram limit is 4096 characters
        _call("sendMessage", data={"chat_id": env("TELEGRAM_CHAT_ID"), "text": text[i:i + 3900]})


def send_video(path, caption=""):
    with open(path, "rb") as f:
        _call("sendVideo", data={"chat_id": env("TELEGRAM_CHAT_ID"), "caption": caption[:1000], "supports_streaming": "true"},
              files={"video": f})


def replies(offset):
    """New text messages from the owner's chat since offset. Returns (messages, new_offset)."""
    ups = _call("getUpdates", data={"offset": offset, "timeout": 0})
    chat = str(env("TELEGRAM_CHAT_ID"))
    msgs = [u["message"]["text"].strip() for u in ups
            if "message" in u and "text" in u["message"] and str(u["message"]["chat"]["id"]) == chat]
    return msgs, (ups[-1]["update_id"] + 1 if ups else offset)
