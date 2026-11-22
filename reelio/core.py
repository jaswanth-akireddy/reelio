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
    v = "".join(os.environ.get(name, "").split())  # keys never contain spaces; strip any pasted by accident
    if required and not v:
        raise SystemExit(f"Missing secret {name}. Add it in GitHub → Settings → Secrets and variables → Actions.")
    return v


def extract_json(text):
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    raw = m.group(1) if m else text[text.find("{"): text.rfind("}") + 1]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # tolerate // comments copied from the prompt and trailing commas
        fixed = re.sub(r"^\s*//.*$", "", raw, flags=re.M)
        fixed = re.sub(r",\s*([}\]])", r"\1", fixed)
        return json.loads(fixed)


def ask_llm(cfg, prompt, search=False, max_tokens=12000):
    """Asks the configured AI and returns its JSON reply, retrying if the JSON is malformed."""
    for attempt in range(3):
        try:
            return _ask_llm(cfg, prompt if attempt == 0 else prompt + "\n\nIMPORTANT: your last reply was not valid JSON. "
                            "Reply with one valid JSON object only; escape any double quotes inside strings.", search, max_tokens)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON from the AI (attempt {attempt + 1}): {e}", flush=True)
    raise RuntimeError("The AI did not return valid JSON after 3 tries")


def _ask_llm(cfg, prompt, search=False, max_tokens=12000):
    provider = cfg["llm"].get("provider", "gemini")
    if provider == "claude_code":
        return extract_json(_claude_code(cfg, prompt, search))
    if provider == "claude":
        return extract_json(_claude(cfg, prompt, search, max_tokens))
    try:
        return extract_json(_gemini(cfg, prompt, search, max_tokens))
    except RuntimeError as e:
        if not search:
            raise
        print("Gemini with Google Search failed, retrying without search:", e, flush=True)
        out = extract_json(_gemini(cfg, prompt + "\n\n(Web search is unavailable: only use facts you are certain of, and mark each fact's source as 'unverified - please check'.)", False, max_tokens))
        out["_no_search"] = True
        return out


ask_claude = ask_llm  # old name


def _gemini(cfg, prompt, search, max_tokens):
    import time
    import requests
    key = env("GEMINI_API_KEY")
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.8}}
    if search and cfg["llm"].get("web_search"):
        body["tools"] = [{"google_search": {}}]
    else:
        body["generationConfig"]["responseMimeType"] = "application/json"
    last = None
    for model in [cfg["llm"]["gemini_model"], cfg["llm"].get("gemini_fallback")]:
        if not model:
            continue
        for attempt in range(3):
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                              headers={"x-goog-api-key": key, "Content-Type": "application/json"}, json=body, timeout=300)
            if r.status_code == 200:
                cands = r.json().get("candidates") or []
                parts = cands[0].get("content", {}).get("parts", []) if cands else []
                text = "".join(p.get("text", "") for p in parts)
                if text.strip():
                    return text
                last = f"{model}: empty reply {r.text[:300]}"
            else:
                last = f"{model}: HTTP {r.status_code} {r.text[:300]}"
                if r.status_code in (429, 500, 503):
                    time.sleep(10 * (attempt + 1))
                    continue
            break
    raise RuntimeError("Gemini failed - " + str(last))


def _claude(cfg, prompt, search, max_tokens):
    import anthropic
    client = anthropic.Anthropic(api_key=env("ANTHROPIC_API_KEY"))
    kwargs = dict(model=cfg["llm"]["claude_model"], max_tokens=max_tokens, messages=[{"role": "user", "content": prompt}])
    if search and cfg["llm"].get("web_search"):
        kwargs["tools"] = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 6}]
    msg = client.messages.create(**kwargs)
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


def _claude_code(cfg, prompt, search):
    """Runs Claude Code headless, signed in with CLAUDE_CODE_OAUTH_TOKEN (your Claude Pro/Max plan, no API bill)."""
    import subprocess
    env("CLAUDE_CODE_OAUTH_TOKEN")
    cmd = ["claude", "-p", "--output-format", "json", "--model", cfg["llm"].get("claude_code_model", "sonnet"), "--max-turns", "15"]
    if search and cfg["llm"].get("web_search"):
        cmd += ["--allowedTools", "WebSearch"]
    p = subprocess.run(cmd, input=prompt + "\n\nReply with the JSON only.", capture_output=True, text=True, timeout=1200)
    try:
        out = json.loads(p.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"Claude Code failed (exit {p.returncode}): {(p.stderr or p.stdout)[-600:]}") from None
    if out.get("is_error") or p.returncode != 0:
        raise RuntimeError(f"Claude Code error: {str(out.get('result', out))[:600]}")
    return out["result"]
