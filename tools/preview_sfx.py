"""Per-cue spectrogram preview -- the audio analogue to sprite-preview.

Renders one PNG per requested cue: stereo waveform on top, log-frequency
STFT spectrogram below, with a stats line (duration / peak / RMS / crest
dB / spectral centroid). Lets you 'see' a procedural cue without ears.

A spectrogram is how audio engineers read sound visually: drones show as
sub-band ridges, harmonics as stacked horizontal stripes, noise bursts as
broadband verticals, filter sweeps as bands moving, reverb tails as energy
decaying after the source, transients as vertical lines. If a cue is HOT,
clipping is visible as flat tops on the waveform; if a tail is too long,
it's visible as energy that won't die in the spectrogram.

Usage (from repo root):
    python tools/preview_sfx.py yk_tone                # one cue
    python tools/preview_sfx.py yk_tone low_pulse      # multiple
    python tools/preview_sfx.py --all                  # every cue
    python tools/preview_sfx.py --out OUT yk_tone      # custom out dir
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


def sound_to_stereo(snd):
    """pygame Sound -> (mono float, L float, R float) in [-1, 1]."""
    arr = pygame.sndarray.array(snd).astype(np.float64) / FULL
    if arr.ndim == 1:
        return arr, arr, arr
    L = arr[:, 0]
    R = arr[:, 1]
    return arr.mean(axis=1), L, R


def measure(mono):
    n = len(mono)
    if n == 0:
        return dict(dur=0, peak=0, rms=0, crest_db=0, centroid=0, clip=0)
    peak = float(np.max(np.abs(mono)))
    rms = float(np.sqrt(np.mean(mono ** 2)))
    crest_db = float(20 * np.log10(peak / rms)) if rms > 1e-9 else 0.0
    clip = float(np.mean(np.abs(mono) >= 0.999))
    if n > 16 and peak > 1e-6:
        win = mono * np.hanning(n)
        mag = np.abs(np.fft.rfft(win))
        freqs = np.fft.rfftfreq(n, 1 / SR)
        centroid = float(np.sum(freqs * mag) / np.sum(mag)) if mag.sum() else 0.0
    else:
        centroid = 0.0
    return dict(dur=n / SR, peak=peak, rms=rms, crest_db=crest_db,
                centroid=centroid, clip=clip)


def render_one(label, snd, out_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm

    mono, L, R = sound_to_stereo(snd)
    m = measure(mono)
    n = len(mono)
    t = np.arange(n) / SR

    # STFT spectrogram. Window short enough for tight time res on short
    # cues (~12ms hop), long enough for some frequency res.
    nperseg = min(1024, max(64, n // 8))
    noverlap = int(nperseg * 0.75)
    f, tt, Sxx = signal.spectrogram(mono, fs=SR, nperseg=nperseg,
                                    noverlap=noverlap, scaling="spectrum")
    # Convert to dB. Floor very quiet bins so log doesn't blow up.
    Sxx_db = 10 * np.log10(np.maximum(Sxx, 1e-10))
    # Display from -80 dB up to 0 dB relative to max.
    vmax = float(Sxx_db.max())
    vmin = vmax - 80.0

    fig = plt.figure(figsize=(9, 5.2), facecolor="#1c1a18")
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 2.2], hspace=0.18)

    # ---- waveform (top) ----
    ax_w = fig.add_subplot(gs[0])
    ax_w.set_facecolor("#262220")
    ax_w.plot(t, L, lw=0.45, color="#ecc840", alpha=0.85, label="L")
    ax_w.plot(t, R, lw=0.45, color="#7ec8e3", alpha=0.65, label="R")
    ax_w.axhline(0, color="#3a3633", lw=0.5)
    ax_w.set_xlim(0, m["dur"] if m["dur"] > 0 else 1)
    ax_w.set_ylim(-1.05, 1.05)
    ax_w.set_xticks([])
    ax_w.tick_params(colors="#9c968f", labelsize=7)
    ax_w.set_ylabel("amp", color="#9c968f", fontsize=8)
    for spine in ax_w.spines.values():
        spine.set_color("#3a3633")

    # ---- spectrogram (bottom) ----
    ax_s = fig.add_subplot(gs[1])
    ax_s.set_facecolor("#100e0c")
    im = ax_s.pcolormesh(tt, f, Sxx_db, cmap="magma",
                          vmin=vmin, vmax=vmax, shading="auto")
    ax_s.set_yscale("symlog", linthresh=30)
    ax_s.set_ylim(20, SR / 2)
    ax_s.set_yticks([30, 100, 300, 1000, 3000, 10000])
    ax_s.set_yticklabels(["30", "100", "300", "1k", "3k", "10k"])
    ax_s.tick_params(colors="#9c968f", labelsize=7)
    ax_s.set_xlabel("time (s)", color="#9c968f", fontsize=8)
    ax_s.set_ylabel("Hz (log)", color="#9c968f", fontsize=8)
    for spine in ax_s.spines.values():
        spine.set_color("#3a3633")
    cbar = fig.colorbar(im, ax=ax_s, pad=0.01, shrink=0.85)
    cbar.set_label("dB", color="#9c968f", fontsize=7)
    cbar.ax.tick_params(colors="#9c968f", labelsize=6)

    # ---- title + stats line ----
    clip_str = f" CLIP {m['clip']*100:.1f}%" if m["clip"] > 0.001 else ""
    title = (f"{label}    "
             f"{m['dur']:.2f}s  peak {m['peak']:.2f}  rms {m['rms']:.2f}  "
             f"crest {m['crest_db']:.0f}dB  centroid {m['centroid']:.0f}Hz"
             f"{clip_str}")
    fig.suptitle(title, color="#ecc840", fontsize=10,
                 fontfamily="monospace", y=0.97)

    fig.savefig(out_path, dpi=110, facecolor=fig.get_facecolor(),
                bbox_inches="tight")
    plt.close(fig)


def collect(audio):
    cues = {}
    for name, snd in audio.sfx.items():
        cues[name] = snd
    for name, snd in audio.music.items():
        cues[f"music__{name}"] = snd
    for attr in ("engine_snd", "radio_snd", "carcosa_drone_snd",
                 "carcosa_roar_snd"):
        snd = getattr(audio, attr, None)
        if snd is not None:
            cues[f"loop__{attr}"] = snd
    return cues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*",
                    help="cue names to render (sfx key or music__X / loop__X)")
    ap.add_argument("--all", action="store_true", help="render every cue")
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "sfx_previews"),
                    help="output directory")
    args = ap.parse_args()

    pygame.init()
    pygame.mixer.init(frequency=SR, size=-16, channels=2)
    from systems.audio import Audio
    audio = Audio()
    cues = collect(audio)

    if args.all:
        names = list(cues.keys())
    elif args.names:
        names = args.names
        missing = [n for n in names if n not in cues]
        if missing:
            print(f"unknown cues: {missing}", file=sys.stderr)
            print(f"available: {sorted(cues.keys())}", file=sys.stderr)
            sys.exit(1)
    else:
        ap.print_help()
        sys.exit(1)

    os.makedirs(args.out, exist_ok=True)
    for name in names:
        path = os.path.join(args.out, f"{name}.png")
        render_one(name, cues[name], path)
        print(f"{name:30} -> {path}")


if __name__ == "__main__":
    main()
