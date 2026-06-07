"""Procedural DSP primitives for THRESHOLD's audio.

Everything here works on numpy float arrays in [-1.0, +1.0] and only
crosses into pygame at the very end via `to_sound`. Audio code lives
in `systems/audio.py`; this module exists so the synth code there can
read like a recipe instead of inlining filter math.

The project ships zero audio assets -- these helpers are what lets the
procedural library carry the body horror without sounding like 1995
chiptune. Filters are scipy biquads; reverb is a Schroeder-style
parallel-comb + series-allpass chain; granular is straight numpy
slicing. None of it streams -- everything is precomputed at startup
or at scene-load time and handed to pygame as a finished Sound.
"""
import numpy as np
from scipy import signal
import pygame

SR = 22050   # The mixer is initialised at this rate in systems/audio.py.


# ---- format conversion --------------------------------------------

def to_sound(sig, vol=1.0):
    """numpy float array (mono or (n, 2) stereo) -> pygame Sound.
    Clips, scales to int16, and duplicates to stereo if mono."""
    sig = np.asarray(sig, dtype=np.float32) * float(vol)
    if sig.ndim == 1:
        sig = np.column_stack([sig, sig])
    sig = np.clip(sig, -1.0, 1.0)
    return pygame.sndarray.make_sound((sig * 32767).astype(np.int16))


# ---- filters (scipy biquads) --------------------------------------

def lowpass(sig, cutoff_hz, order=4):
    sos = signal.butter(order, cutoff_hz, btype="lowpass",
                        fs=SR, output="sos")
    return signal.sosfilt(sos, sig).astype(np.float32)


def highpass(sig, cutoff_hz, order=4):
    sos = signal.butter(order, cutoff_hz, btype="highpass",
                        fs=SR, output="sos")
    return signal.sosfilt(sos, sig).astype(np.float32)


# ---- reverb (Schroeder: 4 parallel combs -> 2 series allpasses) ---

def _comb(sig, delay_samples, feedback):
    """Single feedback-comb. Returns same length as input."""
    out = np.zeros_like(sig)
    buf = np.zeros(delay_samples, dtype=np.float32)
    bi = 0
    for i in range(len(sig)):
        delayed = buf[bi]
        out[i] = delayed
        buf[bi] = sig[i] + delayed * feedback
        bi = (bi + 1) % delay_samples
    return out


def _allpass(sig, delay_samples, gain=0.5):
    out = np.zeros_like(sig)
    buf = np.zeros(delay_samples, dtype=np.float32)
    bi = 0
    for i in range(len(sig)):
        delayed = buf[bi]
        v = -gain * sig[i] + delayed
        buf[bi] = sig[i] + gain * v
        out[i] = v
        bi = (bi + 1) % delay_samples
    return out


# Per-space reverb profiles. tail_s is added to the input length so
# the reverb tail isn't cut off when the dry sample ends. Combs are
# four mutually-prime-ish delays so the tail is dense rather than
# metallic; allpasses break any remaining periodicity.
_REVERB_PROFILES = {
    # Tight, small wood interiors (lodge rooms, kitchens). Almost no
    # tail -- just a touch of room acoustic so dry foley doesn't feel
    # naked.
    "room": dict(combs=[(29, 0.55), (37, 0.50), (41, 0.45), (43, 0.40)],
                 allpasses=[(13, 0.5), (7, 0.5)], wet=0.18, tail_s=0.15),
    # Large stone cellars + the Works. Long reverberant tail, lots of
    # high-end damping. This is where you stand and the floor sounds
    # like it's a long way down.
    "cellar": dict(combs=[(53, 0.78), (61, 0.74), (67, 0.70), (71, 0.66)],
                   allpasses=[(23, 0.55), (11, 0.55)], wet=0.35,
                   tail_s=0.9, hp_after=120),
    # Open outdoor (cornfield, brimley). No reflective surfaces;
    # almost no reverb, but a very subtle slap-back so wide spaces
    # don't sound the same as inside a closet.
    "outdoor": dict(combs=[(89, 0.30), (97, 0.25)], allpasses=[(19, 0.4)],
                    wet=0.08, tail_s=0.20),
    # The Depths / void. Long, low, wrong.
    "void": dict(combs=[(67, 0.85), (79, 0.82), (89, 0.79), (97, 0.76)],
                 allpasses=[(31, 0.6), (17, 0.6)], wet=0.45, tail_s=1.6,
                 lp_after=900),
}


def reverb(sig, profile="room"):
    """Apply a Schroeder reverb in the named space. Always returns a
    longer signal (input + tail). No-op for unknown profiles."""
    p = _REVERB_PROFILES.get(profile)
    if p is None:
        return sig
    sig = np.asarray(sig, dtype=np.float32)
    tail_pad = np.zeros(int(SR * p["tail_s"]), dtype=np.float32)
    padded = np.concatenate([sig, tail_pad])
    # Four combs in parallel, summed.
    wet = np.zeros_like(padded)
    for d_ms, fb in p["combs"]:
        wet += _comb(padded, int(SR * d_ms / 1000), fb)
    wet /= max(1, len(p["combs"]))
    # Allpasses in series to smear what's left.
    for d_ms, g in p["allpasses"]:
        wet = _allpass(wet, int(SR * d_ms / 1000), g)
    # Optional post-EQ on the wet tail (HP to keep big spaces from
    # muddying; LP to make the void feel like it's behind a wall).
    if p.get("hp_after"):
        wet = highpass(wet, p["hp_after"], order=2)
    if p.get("lp_after"):
        wet = lowpass(wet, p["lp_after"], order=2)
    return padded + wet * p["wet"]

