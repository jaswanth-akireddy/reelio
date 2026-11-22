"""ElevenLabs narration with character timings, turned into a word-timed timeline for the renderer."""
import base64
import json

import requests

from .core import env

LEAD_IN = 0.35   # seconds of silence before the voice starts
TAIL = 1.6       # seconds held on the end card after the voice ends


def spoken_words(script):
    """All (native, roman, beat_index) triples in order."""
    return [(w[0], w[1], bi) for bi, b in enumerate(script["beats"]) for w in b["words"]]


def synthesize(cfg, script, out_audio):
    """Calls ElevenLabs once for the whole script. Returns (duration, per-word (start, end))."""
    v = cfg["voice"]
    words = spoken_words(script)
    text = " ".join(w[0] for w in words)
    r = _tts(v, v["voice_id"], text)
    if r.status_code == 402 and v.get("fallback_voice_id") and v["fallback_voice_id"] != v["voice_id"]:
        print("Voice needs a paid plan; using the fallback voice", flush=True)
        r = _tts(v, v["fallback_voice_id"], text)
    if r.status_code != 200:
        raise RuntimeError(f"ElevenLabs error {r.status_code}: {r.text[:500]}")
    data = r.json()
    with open(out_audio, "wb") as f:
        f.write(base64.b64decode(data["audio_base64"]))
    al = data.get("alignment") or data.get("normalized_alignment")
    return word_times(text, words, al)


def _tts(v, voice_id, text):
    return requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps",
        headers={"xi-api-key": env("ELEVENLABS_API_KEY"), "Content-Type": "application/json"},
        params={"output_format": "mp3_44100_128"},
        json={"text": text, "model_id": v["model_id"], "language_code": "te",
              "voice_settings": {"stability": v["stability"], "similarity_boost": v["similarity_boost"], "speed": v.get("speed", 1.0)}},
        timeout=300)


def word_times(text, words, al):
    starts, ends, chars = al["character_start_times_seconds"], al["character_end_times_seconds"], al["characters"]
    duration = ends[-1]
    spans, pos = [], 0
    for w in words:
        spans.append((pos, pos + len(w[0])))
        pos += len(w[0]) + 1
    if "".join(chars) == text:
        times = [(starts[a], ends[b - 1]) for a, b in spans]
    else:  # alignment text differs (normalisation) - fall back to proportional timing
        times = [(duration * a / len(text), duration * b / len(text)) for a, b in spans]
    return duration, times


def fake_times(script, wps=2.4):
    """Offline timings for dry runs without the API."""
    t, times = 0.0, []
    for _, roman, _ in spoken_words(script):
        d = 0.15 + 0.055 * len(roman)
        times.append((t, t + d))
        t += d + (0.28 if roman[-1:] in ".?!" else 0.12 if roman[-1:] == "," else 0.02)
    return t, times


def build_timeline(cfg, script, duration, times):
    words = spoken_words(script)
    beats = []
    for bi, b in enumerate(script["beats"]):
        ws = [{"w": roman, "start": round(LEAD_IN + s, 3), "end": round(LEAD_IN + e, 3)}
              for (native, roman, wb), (s, e) in zip(words, times) if wb == bi]
        if not ws:
            continue
        beats.append({"scene": b["scene"], "words": ws, "title": b.get("title"), "label": b.get("label"), "card": b.get("card")})
    if beats and beats[-1]["scene"] != "hero_cta":
        beats[-1]["scene"] = "hero_cta"
    ch = cfg["channel"]
    return {"end": round(LEAD_IN + duration + TAIL, 3), "handle": ch["handle"], "series": ch["series"],
            "series_sub": ch.get("series_sub", ""), "beats": beats}


def save(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
