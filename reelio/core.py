"""Config, Claude calls, and JSON helpers."""
import json
import os
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_config():
    return yaml.safe_load((ROOT / "config.yaml").read_text())


def env(name, required=True):
    v = os.environ.get(name, "").strip()
    if required and not v:
        raise SystemExit(f"Missing secret {name}. Add it in GitHub → Settings → Secrets and variables → Actions.")
    return v


def extract_json(text):
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    raw = m.group(1) if m else text[text.find("{"): text.rfind("}") + 1]
    raw = re.sub(r"//[^\n\"]*$", "", raw, flags=re.M)  # tolerate // comments copied from the prompt
    return json.loads(raw)


def ask_claude(cfg, prompt, search=False, max_tokens=12000):
    import anthropic
    client = anthropic.Anthropic(api_key=env("ANTHROPIC_API_KEY"))
    kwargs = dict(model=cfg["llm"]["model"], max_tokens=max_tokens, messages=[{"role": "user", "content": prompt}])
    if search and cfg["llm"].get("web_search"):
        kwargs["tools"] = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 6}]
    msg = client.messages.create(**kwargs)
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    return extract_json(text)
