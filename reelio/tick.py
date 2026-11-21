"""One step of the daily pipeline. GitHub Actions runs this every 15 minutes.

Stages (saved in state/state.json):
  idle -> await_pick -> await_script -> await_publish -> idle
You steer it from Telegram:
  /ideas         start a new video now          1..5     pick an idea
  ok             approve the script             any text revise the script with that feedback
  publish        post the approved video        redo ... rewrite the script with feedback
  /status        where things are               /cancel  drop the current video
"""
import datetime as dt
import json
import subprocess
from pathlib import Path

from . import prompts, telegram, youtube
from .core import ROOT, ask_llm, load_config

STATE = ROOT / "state" / "state.json"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def load():
    return json.loads(STATE.read_text())


def save(s):
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=1))


def script_message(sc):
    lines = [f"📝 SCRIPT: {sc['topic']}", f"Hook score: {sc.get('hook_score', '?')}/10", ""]
    for i, b in enumerate(sc["beats"], 1):
        te = " ".join(w[0] for w in b["words"])
        ro = " ".join(w[1] for w in b["words"])
        title = (b.get("title") or {}).get("text", "")
        lines += [f"{i}. [{b['scene']}] {title}", f"   {te}", f"   ({ro})", f"   ↳ {b.get('retention', '')}", ""]
    if sc.get("predicted_retention_risks"):
        lines += ["⚠️ Swipe-away risks:"] + [f"• {r}" for r in sc["predicted_retention_risks"]] + [""]
    if sc.get("_no_search"):
        lines += ["⚠️ Facts were NOT web-checked this time (search quota). Please verify the numbers below.", ""]
    if sc.get("facts"):
        lines += ["🔎 Facts to double-check:"] + [f"• {f['claim']} — {f.get('source', '')}" for f in sc["facts"]] + [""]
    lines += [f"YouTube title: {sc.get('youtube_title', '')}", "", "Reply 'ok' to make the video, or type changes you want."]
    return "\n".join(lines)


def start_ideas(cfg, s):
    ideas = ask_llm(cfg, prompts.ideas_prompt(cfg, s.get("history", [])[-15:]))["ideas"][:5]
    for i in ideas:
        sc = i["scores"]
        i["total"] = sc["hook"] + sc["curiosity"] + sc["fit_3d"] + sc["shareability"]
    ideas.sort(key=lambda i: -i["total"])
    msg = ["💡 Today's ideas (scores: hook / curiosity / 3D fit / shareability):", ""]
    for n, i in enumerate(ideas, 1):
        sc = i["scores"]
        msg += [f"{n}. {i['topic']} — {i['angle']}", f"   Hook: \"{i['hook_line_en']}\"",
                f"   {sc['hook']}/{sc['curiosity']}/{sc['fit_3d']}/{sc['shareability']}  (total {i['total']}/40)", f"   {i['why']}", ""]
    msg.append("Reply with a number to pick one.")
    telegram.send("\n".join(msg))
    s.update(stage="await_pick", ideas=ideas, date=dt.datetime.now(IST).date().isoformat())


def write_script(cfg, s, feedback=None):
    telegram.send("✍️ Writing the script (checking facts too)…" if not feedback else "✍️ Revising…")
    sc = ask_llm(cfg, prompts.script_prompt(cfg, s["idea"], feedback, s.get("script") if feedback else None), search=True)
    s.update(stage="await_script", script=sc)
    telegram.send(script_message(sc))


def make_video(cfg, s, run_id):
    telegram.send("🎙️ Recording the voice and rendering the 3D video. This takes about 15 minutes…")
    from .produce import produce
    work = ROOT / "work"
    final, _ = produce(cfg, s["script"], work)
    tag = f"video-{run_id}"
    subprocess.run(["gh", "release", "create", tag, str(final), "--prerelease", "--title", s["script"]["topic"],
                    "--notes", s["script"].get("youtube_title", "")], check=True)
    s.update(stage="await_publish", release=tag)
    telegram.send_video(final, caption=f"🎬 {s['script'].get('youtube_title', '')}")
    telegram.send("Reply 'publish' to post it, or 'redo <what to change>' to rewrite.")


def publish(cfg, s):
    out = ROOT / "work"
    out.mkdir(exist_ok=True)
    subprocess.run(["gh", "release", "download", s["release"], "-D", str(out), "--clobber"], check=True)
    path = next(out.glob("*.mp4"))
    sc, links = s["script"], []
    if cfg["publish"]["youtube"] and youtube.configured():
        links.append(youtube.upload(path, sc["youtube_title"], sc.get("description", ""), cfg["publish"]["youtube_privacy"]))
    else:
        links.append("YouTube skipped (add the YOUTUBE_* secrets to enable it)")
    if cfg["publish"].get("instagram"):
        links.append("Instagram posting is not built yet — download the video from Telegram and post it manually.")
    telegram.send("✅ Done!\n" + "\n".join(links))
    s.setdefault("history", []).append(sc["topic"])
    for k in ("ideas", "idea", "script", "release"):
        s.pop(k, None)
    s["stage"] = "idle"


def needs_run():
    """Cheap check used by the first workflow job: is there anything to do?"""
    cfg, s = load_config(), load()
    now = dt.datetime.now(IST)
    if s["stage"] == "idle" and s.get("date") != now.date().isoformat() and now.hour >= cfg["schedule"]["ideas_hour_ist"]:
        return True
    if s["stage"] == "await_pick" and s.get("idea") and not s.get("script"):
        return True
    ups = telegram._call("getUpdates", data={"offset": s.get("tg_offset", 0), "timeout": 0})  # peeks without consuming
    return any(str(u.get("message", {}).get("chat", {}).get("id")) == str(telegram.env("TELEGRAM_CHAT_ID")) for u in ups)


def main():
    import os
    import sys
    if "--check" in sys.argv:
        need = needs_run()
        print("need =", need)
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write(f"need={'true' if need else 'false'}\n")
        return
    cfg = load_config()
    s = load()
    msgs, s["tg_offset"] = telegram.replies(s.get("tg_offset", 0))
    save(s)  # never re-read the same messages, even if a later step fails
    run_id = os.environ.get("GITHUB_RUN_ID", "local")
    now = dt.datetime.now(IST)
    try:
        for m in msgs:
            low = m.lower().strip()
            if low == "/status":
                telegram.send(f"Stage: {s['stage']}" + (f" — {s['idea']['topic']}" if s.get("idea") else ""))
            elif low == "/cancel":
                s.update(stage="idle")
                telegram.send("Cancelled. Send /ideas to start again.")
            elif low == "/ideas":
                start_ideas(cfg, s)
            elif s["stage"] == "await_pick" and low.isdigit() and 1 <= int(low) <= len(s["ideas"]):
                s["idea"] = s["ideas"][int(low) - 1]
                write_script(cfg, s)
            elif s["stage"] == "await_script":
                if low in ("ok", "okay", "approve", "yes"):
                    make_video(cfg, s, run_id)
                else:
                    write_script(cfg, s, feedback=m)
            elif s["stage"] == "await_publish":
                if low == "publish":
                    publish(cfg, s)
                elif low.startswith("redo"):
                    write_script(cfg, s, feedback=m[4:].strip() or "make it better")
            save(s)
        if s["stage"] == "await_pick" and s.get("idea") and not s.get("script"):  # resume a pick whose script failed
            write_script(cfg, s)
            save(s)
        if s["stage"] == "idle" and s.get("date") != now.date().isoformat() and now.hour >= cfg["schedule"]["ideas_hour_ist"]:
            start_ideas(cfg, s)
    except Exception as e:
        telegram.send(f"❌ Something failed at stage '{s['stage']}': {e}\nCheck the Actions log on GitHub.")
        raise
    finally:
        save(s)


if __name__ == "__main__":
    main()
