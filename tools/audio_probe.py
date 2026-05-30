"""Audio probe -- judge THRESHOLD's procedural sound headlessly.

The whole audio library is synthesised in code (systems/audio.py); there
are no .wav files to open and, in a web/CI session, nothing to listen to.
This tool builds the library, then for every cue:

  * EXPORTS it to a real .wav (so it can be auditioned / shared), and
  * MEASURES it -- duration, peak, RMS loudness, crest factor, clipping,
    DC offset, and spectral centroid (brightness) -- and FLAGS the ones
    that are objectively off (clipping, near-silent, DC-biased, harsh, or
    sub-only so they vanish on laptop speakers).

It can't tell you if a cue is *scary* -- that's ears-on -- but it catches
the things that make procedural audio sound cheap, and gives a reviewer a
data floor under the subjective call.

Usage (from repo root):
    python tools/audio_probe.py                # report only
    python tools/audio_probe.py --wav out/dir  # also export WAVs
    python tools/audio_probe.py --png          # waveform montage PNG
"""
import argparse
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import numpy as np
import pygame

SR = 22050
FULL = 32767.0


def collect_cues(audio):
    """Return an ordered {label: Sound} map of every audible cue: SFX,
    music loops, and the standalone drive/ending loops."""
    cues = {}
    for name, snd in sorted(audio.sfx.items()):
        cues[f"sfx/{name}"] = snd
    for name, snd in sorted(audio.music.items()):
        cues[f"music/{name}"] = snd
    for attr in ("engine_snd", "radio_snd", "carcosa_drone_snd",
                 "carcosa_roar_snd"):
        snd = getattr(audio, attr, None)
        if snd is not None:
            cues[f"loop/{attr}"] = snd
    return cues


def measure(snd):
    arr = pygame.sndarray.array(snd).astype(np.float64)
    mono = arr.mean(axis=1) if arr.ndim == 2 else arr
    n = len(mono)
    dur = n / SR
    norm = mono / FULL
    peak = float(np.max(np.abs(norm))) if n else 0.0
    rms = float(np.sqrt(np.mean(norm ** 2))) if n else 0.0
    crest_db = 20 * np.log10(peak / rms) if rms > 1e-9 else float("inf")
    clip = float(np.mean(np.abs(mono) >= FULL * 0.999)) if n else 0.0
    dc = float(np.mean(norm)) if n else 0.0
    # Spectral centroid (Hz) -- a brightness proxy.
    if n > 16 and peak > 1e-6:
        win = mono * np.hanning(n)
        mag = np.abs(np.fft.rfft(win))
        freqs = np.fft.rfftfreq(n, 1 / SR)
        centroid = float(np.sum(freqs * mag) / np.sum(mag)) if mag.sum() else 0.0
    else:
        centroid = 0.0
    return dict(dur=dur, peak=peak, rms=rms, crest_db=crest_db,
                clip=clip, dc=dc, centroid=centroid)


def flags(m):
    out = []
    if m["clip"] > 0.001:
        out.append(f"CLIP({m['clip']*100:.1f}%)")
    if m["peak"] >= 0.995 and m["clip"] <= 0.001:
        out.append("HOT")
    if m["peak"] < 0.03:
        out.append("NEAR-SILENT")
    if abs(m["dc"]) > 0.02:
        out.append(f"DC({m['dc']:+.2f})")
    if m["centroid"] > 5000:
        out.append("HARSH")
    if 0 < m["centroid"] < 110:
        out.append("SUB-ONLY")
    return out


def export_wav(snd, path):
    from scipy.io import wavfile
    arr = pygame.sndarray.array(snd).astype(np.int16)
    wavfile.write(path, SR, arr)


def montage_png(cues, path):
    try:
        import matplotlib
    except ImportError:
        print("montage skipped: matplotlib not installed "
              "(pip install matplotlib)")
        return
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    items = list(cues.items())
    cols = 4
    rows = (len(items) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 3.2, rows * 1.3))
    fig.patch.set_facecolor("#1c1a18")
    for ax, (label, snd) in zip(axes.flat, items):
        arr = pygame.sndarray.array(snd).astype(np.float64)
        mono = (arr.mean(axis=1) if arr.ndim == 2 else arr) / FULL
        ax.plot(mono, lw=0.4, color="#ecc840")
        ax.set_ylim(-1, 1)
        ax.set_facecolor("#262220")
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(label, fontsize=6, color="#cfcadf")
    for ax in axes.flat[len(items):]:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=120, facecolor=fig.get_facecolor())
    print(f"montage -> {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wav", metavar="DIR", help="export every cue as a WAV here")
    ap.add_argument("--png", action="store_true", help="waveform montage PNG")
    args = ap.parse_args()

    pygame.init()
    pygame.mixer.init(frequency=SR, size=-16, channels=2)
    from systems.audio import Audio
    audio = Audio()
    cues = collect_cues(audio)

    print(f"{'cue':28} {'dur':>5} {'peak':>5} {'rms':>5} "
          f"{'crest':>6} {'cent.Hz':>8}  flags")
    print("-" * 78)
    issues = 0
    for label, snd in cues.items():
        m = measure(snd)
        fl = flags(m)
        issues += bool(fl)
        crest = "inf" if m["crest_db"] == float("inf") else f"{m['crest_db']:.0f}"
        print(f"{label:28} {m['dur']:5.2f} {m['peak']:5.2f} {m['rms']:5.2f} "
              f"{crest:>6} {m['centroid']:8.0f}  {' '.join(fl)}")

    print("-" * 78)
    print(f"{len(cues)} cues, {issues} flagged.")

    if args.wav:
        os.makedirs(args.wav, exist_ok=True)
        for label, snd in cues.items():
            fn = label.replace("/", "__") + ".wav"
            export_wav(snd, os.path.join(args.wav, fn))
        print(f"exported {len(cues)} WAVs -> {args.wav}")
    if args.png:
        montage_png(cues, os.path.join(ROOT, "tools", "audio_waveforms.png"))


if __name__ == "__main__":
    main()
