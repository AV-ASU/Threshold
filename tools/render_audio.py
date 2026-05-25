"""Headless audio auditioner for THRESHOLD.

Renders the procedurally-synthesized SFX to .wav files you can actually
play -- the audio analog of tools/render_scenes.py. The build/CI box has
no audio device (SDL_AUDIODRIVER=dummy), so sounds get written blind;
this tool lets you (or a reviewer with speakers) listen to and tune them
without launching the game.

It drives the real systems.audio.Audio synth, so what you hear is exactly
what the game plays. The mixer runs at 22050 Hz, 16-bit, stereo.

Usage (from the repo root):
    python tools/render_audio.py                 # every SFX -> /tmp/threshold_audio
    python tools/render_audio.py screech         # only these names
    python tools/render_audio.py --list          # print every SFX name
    python tools/render_audio.py --out /path/x   # custom output dir
    python tools/render_audio.py --seq screech yk_tone alarm_bell
                                                 # + a stitched compare.wav

Output: <out>/<name>.wav  (default out: /tmp/threshold_audio)
With --seq, also <out>/_compare.wav -- the requested sounds back to back
with a short gap, for A/B listening (e.g. screech vs the King's yk_tone).
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import sys
import wave

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import pygame
pygame.init()

from systems.audio import Audio

SR = 22050          # systems.audio._gen's sample rate
CHANNELS = 2
SAMPWIDTH = 2       # 16-bit
GAP_S = 0.35        # silence between sounds in the stitched compare file


def _write_wav(path, raw):
    with wave.open(path, "wb") as w:
        w.setnchannels(CHANNELS)
        w.setsampwidth(SAMPWIDTH)
        w.setframerate(SR)
        w.writeframes(raw)


def _parse_args(argv):
    out = "/tmp/threshold_audio"
    names = []
    do_list = False
    do_seq = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--out" and i + 1 < len(argv):
            out = argv[i + 1]
            i += 2
        elif a == "--list":
            do_list = True
            i += 1
        elif a == "--seq":
            do_seq = True
            i += 1
        else:
            names.append(a)
            i += 1
    return out, names, do_list, do_seq


def main():
    out, names, do_list, do_seq = _parse_args(sys.argv[1:])
    audio = Audio()
    if not audio.enabled or not audio.sfx:
        print("ERROR: audio synth did not initialise (no SFX library built).")
        return 1
    if do_list:
        for k in sorted(audio.sfx):
            print(k)
        return 0

    keys = names or sorted(audio.sfx)
    os.makedirs(out, exist_ok=True)
    saved = []
    gap = b"\x00" * int(GAP_S * SR) * CHANNELS * SAMPWIDTH
    seq_chunks = []
    for k in keys:
        snd = audio.sfx.get(k)
        if snd is None:
            print(f"SKIP (no such sfx): {k}")
            continue
        raw = snd.get_raw()
        path = os.path.join(out, f"{k}.wav")
        _write_wav(path, raw)
        saved.append(path)
        seq_chunks.append(raw)

    if do_seq and len(seq_chunks) > 1:
        stitched = gap.join(seq_chunks)
        cmp_path = os.path.join(out, "_compare.wav")
        _write_wav(cmp_path, stitched)
        saved.append(cmp_path)

    print(f"wrote {len(saved)} wav(s) -> {out}")
    for p in saved:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
