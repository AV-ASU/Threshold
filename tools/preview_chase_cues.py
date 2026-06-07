"""One-shot composite preview of the chase-loop cues -- waveform + log
Mel-ish spectrogram for cult_lock, cult_lose, watcher_spawn, watcher_dispel,
hide_enter, hide_exit, stacked vertically with stats per cue.

Usage:
    python tools/preview_chase_cues.py
    python tools/preview_chase_cues.py --out PATH.png
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
from scipy import signal

SR = 22050
FULL = 32767.0

CHASE_CUES = ["cult_lock", "cult_lose",
              "watcher_spawn", "watcher_dispel",
              "hide_enter", "hide_exit"]


def mono(snd):
    arr = pygame.sndarray.array(snd).astype(np.float64) / FULL
    return arr.mean(axis=1) if arr.ndim == 2 else arr


def stats(m):
    n = len(m)
    peak = float(np.max(np.abs(m))) if n else 0.0
    rms = float(np.sqrt(np.mean(m ** 2))) if n else 0.0
    crest = 20 * np.log10(peak / rms) if rms > 1e-9 else 0.0
    if n > 16 and peak > 1e-6:
        win = m * np.hanning(n)
        mag = np.abs(np.fft.rfft(win))
        freqs = np.fft.rfftfreq(n, 1 / SR)
        cent = float(np.sum(freqs * mag) / np.sum(mag)) if mag.sum() else 0.0
    else:
        cent = 0.0
    return dict(dur=n / SR, peak=peak, rms=rms, crest=crest, cent=cent)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "tools",
                                                   "chase_cues.png"))
    args = ap.parse_args()

    pygame.init()
    pygame.mixer.init(frequency=SR, size=-16, channels=2)
    from systems.audio import Audio
    audio = Audio()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n_cues = len(CHASE_CUES)
    fig = plt.figure(figsize=(12, n_cues * 1.9), facecolor="#1c1a18")
    gs = fig.add_gridspec(n_cues, 2, width_ratios=[1, 2.6],
                          hspace=0.55, wspace=0.12)

    for row, name in enumerate(CHASE_CUES):
        snd = audio.sfx[name]
        sig = mono(snd)
        st = stats(sig)
        t = np.arange(len(sig)) / SR

        # waveform (left)
        ax_w = fig.add_subplot(gs[row, 0])
        ax_w.set_facecolor("#262220")
        ax_w.plot(t, sig, lw=0.5, color="#ecc840")
        ax_w.axhline(0, color="#3a3633", lw=0.5)
        ax_w.set_xlim(0, st["dur"])
        ax_w.set_ylim(-0.5, 0.5)
        ax_w.tick_params(colors="#9c968f", labelsize=6)
        ax_w.set_xlabel("s", color="#9c968f", fontsize=7)
        for sp in ax_w.spines.values():
            sp.set_color("#3a3633")
        ax_w.set_title(
            f"{name}", color="#ecc840", fontsize=10,
            fontfamily="monospace", loc="left")

        # spectrogram (right)
        ax_s = fig.add_subplot(gs[row, 1])
        ax_s.set_facecolor("#100e0c")
        nperseg = min(1024, max(64, len(sig) // 8))
        noverlap = int(nperseg * 0.75)
        f, tt, Sxx = signal.spectrogram(sig, fs=SR, nperseg=nperseg,
                                        noverlap=noverlap,
                                        scaling="spectrum")
        Sxx_db = 10 * np.log10(np.maximum(Sxx, 1e-10))
        vmax = float(Sxx_db.max())
        vmin = vmax - 80.0
        ax_s.pcolormesh(tt, f, Sxx_db, cmap="magma",
                        vmin=vmin, vmax=vmax, shading="auto")
        ax_s.set_yscale("symlog", linthresh=30)
        ax_s.set_ylim(20, SR / 2)
        ax_s.set_yticks([30, 100, 300, 1000, 3000, 10000])
        ax_s.set_yticklabels(["30", "100", "300", "1k", "3k", "10k"])
        ax_s.tick_params(colors="#9c968f", labelsize=6)
        for sp in ax_s.spines.values():
            sp.set_color("#3a3633")
        ax_s.set_xlabel("s", color="#9c968f", fontsize=7)
        ax_s.set_ylabel("Hz", color="#9c968f", fontsize=7)
        ax_s.set_title(
            f"  {st['dur']:.2f}s   peak {st['peak']:.2f}   "
            f"rms {st['rms']:.2f}   crest {st['crest']:.0f}dB   "
            f"centroid {st['cent']:.0f}Hz",
            color="#cfcadf", fontsize=8, fontfamily="monospace",
            loc="left")

    fig.suptitle("THRESHOLD chase-loop cues", color="#ecc840",
                 fontsize=13, fontfamily="monospace", y=0.995)
    fig.savefig(args.out, dpi=110, facecolor=fig.get_facecolor(),
                bbox_inches="tight")
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
