"""Render a sample script offline (no API keys): python scripts/dry_run.py [samples/abs_te.json] [--stills 2,10,20]"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from reelio import voice  # noqa: E402
from reelio.core import ROOT, load_config  # noqa: E402

argv = sys.argv[1:]
if "--stills" in argv:
    i = argv.index("--stills")
    argv = argv[:i] + argv[i + 2:]
args = [a for a in argv if not a.startswith("--")]
script = json.loads(Path(args[0] if args else ROOT / "samples/abs_te.json").read_text())
cfg = load_config()
work = ROOT / "work" / "dry"
work.mkdir(parents=True, exist_ok=True)
if "--stills" in sys.argv:
    dur, times = voice.fake_times(script)
    voice.save(work / "timeline.json", voice.build_timeline(cfg, script, dur, times))
    subprocess.run(["node", str(ROOT / "template/render.js"), str(work / "timeline.json"), "--stills",
                    sys.argv[sys.argv.index("--stills") + 1], str(work / "stills")], check=True)
    print("stills in", work / "stills")
else:
    from reelio.produce import produce
    final, tl = produce(cfg, script, work, fake_voice=True)
    print("video:", final, f"({tl['end']:.1f}s)")
