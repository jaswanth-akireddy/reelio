"""Voice → timeline → 3D render → music mix → final MP4."""
import subprocess
from pathlib import Path

import numpy as np
import scipy.io.wavfile as wavfile

from . import voice
from .core import ROOT


def music_bed(seconds, path, seed=1):
    """Generates a quiet, royalty-free ambient bed (no licence worries)."""
    sr = 44100
    n = int(sr * seconds)
    t = np.arange(n) / sr
    note = lambda m: 440 * 2 ** ((m - 69) / 12)
    bpm = 96
    beat, bar = 60 / bpm, 240 / bpm
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    out = np.zeros(n)
    for i in range(int(seconds / bar) + 1):
        a, b = int(i * bar * sr), min(n, int((i * bar + bar + 0.6) * sr))
        if a >= n:
            break
        tt = np.arange(b - a) / sr
        env = np.minimum(1, tt / 0.8) * np.minimum(1, (tt[-1] - tt) / 0.8 + 1e-3)
        for m in chords[i % 4]:
            out[a:b] += env * np.sin(2 * np.pi * note(m) * tt) * 0.06
        out[a:b] += env * np.sin(2 * np.pi * note(chords[i % 4][0] - 12) * tt) * 0.08
    for j in range(int(seconds / (beat / 2))):
        a, L = int(j * beat / 2 * sr), int(0.35 * sr)
        if a + L > n:
            break
        tt = np.arange(L) / sr
        out[a:a + L] += np.sin(2 * np.pi * note(chords[int(j * beat / 2 / bar) % 4][j % 3] + 12) * tt) * np.exp(-tt * 9) * 0.05
    for j in range(int(seconds / beat)):
        a, L = int(j * beat * sr), int(0.25 * sr)
        if a + L > n:
            break
        tt = np.arange(L) / sr
        out[a:a + L] += np.sin(2 * np.pi * np.cumsum(50 + 60 * np.exp(-tt * 30)) / sr) * np.exp(-tt * 14) * 0.2
    out *= np.minimum(1, t / 1.0) * np.minimum(1, (seconds - t) / 1.5)
    out /= np.abs(out).max() / 0.6
    wavfile.write(path, sr, (np.stack([out, out], 1) * 32767).astype(np.int16))


def run(cmd):
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.run(cmd, check=True)


def produce(cfg, script, work: Path, fake_voice=False):
    work.mkdir(parents=True, exist_ok=True)
    audio = work / "voice.mp3"
    if fake_voice:
        duration, times = voice.fake_times(script)
        audio = None
    else:
        duration, times = voice.synthesize(cfg, script, audio)
    tl = voice.build_timeline(cfg, script, duration, times)
    voice.save(work / "timeline.json", tl)
    silent = work / "silent.mp4"
    run(["node", str(ROOT / "template/render.js"), str(work / "timeline.json"), str(silent), str(cfg["video"]["render_workers"])])
    music_bed(tl["end"], work / "music.wav")
    final = work / "final.mp4"
    vol = cfg["video"]["music_volume"]
    if audio:
        fc = (f"[1:a]adelay={int(voice.LEAD_IN * 1000)}:all=1,apad[v];[2:a]volume={vol}[m];"
              f"[m][v]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[md];[v][md]amix=inputs=2:duration=longest:normalize=0[a]")
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", audio, "-i", work / "music.wav", "-filter_complex", fc,
             "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", final])
    else:
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", work / "music.wav", "-map", "0:v", "-map", "1:a",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", final])
    return final, tl
