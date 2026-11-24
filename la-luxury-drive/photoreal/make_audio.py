"""
Bande son 100 % synthétisée (aucun fichier externe, libre de droits) :
  - musique synthwave originale (pads, basse, arpèges, batterie)
  - moteurs des voitures calculés depuis les trajectoires réelles de chaque plan
    (volume selon la distance, effet Doppler, régime selon la vitesse)
Usage : python make_audio.py <timeline.json> <out.wav>
"""
import json, math, os, sys, wave
import numpy as np

SR = 44100
timeline = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
TOTAL = timeline["total"]
N = int(TOTAL * SR)
rng = np.random.default_rng(3)

# ------------------------------------------------------------------ outils
def env_adsr(n, a=0.01, d=0.1, s=0.7, r=0.2):
    e = np.ones(n) * s
    ia, idd, ir = int(a * SR), int(d * SR), int(r * SR)
    ia = min(ia, n); e[:ia] = np.linspace(0, 1, ia)
    idd = min(idd, n - ia); e[ia:ia + idd] = np.linspace(1, s, idd)
    ir = min(ir, n); e[n - ir:] *= np.linspace(1, 0, ir)
    return e

def saw(freq, n, detune=0.0):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for dt in (-detune, 0, detune):
        ph = (t * freq * (1 + dt)) % 1.0
        out += 2 * ph - 1
    return out / 3

def lp_fast(x, cutoff):
    """passe-bas 1 pôle, par convolution avec un noyau exponentiel tronqué."""
    a = math.exp(-2 * math.pi * cutoff / SR)
    k = int(min(4000, max(4, math.log(1e-4) / math.log(a))))
    w = (1 - a) * a ** np.arange(k)
    return np.convolve(x, w)[:len(x)]

def note(n):  # n = numéro MIDI
    return 440.0 * 2 ** ((n - 69) / 12)

# ------------------------------------------------------------------ musique
BPM = 96.0
beat = 60.0 / BPM
bar = 4 * beat
music = np.zeros(N)
# progression (la mineur) : Am - F - C - G
prog = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [48, 52, 55]), (55, [55, 59, 62])]
acts = timeline["acts"]          # [(start, end, name)]
def intensity(t):
    """0 = intro calme, 1 = tension, 2 = course."""
    for st, en, name in acts:
        if st <= t < en:
            return {"coast": 1, "desert": 1, "track": 2, "canyon": 0}[name] if t > 6 else 0
    return 0

nbars = int(TOTAL / bar) + 1
for b in range(nbars):
    t0 = b * bar
    if t0 >= TOTAL: break
    root, chord = prog[b % 4]
    lvl = intensity(t0)
    i0 = int(t0 * SR); nb = int(bar * SR)
    if i0 + nb > N: nb = N - i0
    # pad
    pad = sum(saw(note(n + 12), nb, 0.004) for n in chord) / 3
    pad = lp_fast(pad, 1400 if lvl < 2 else 2200) * env_adsr(nb, 0.6, 0.3, 0.8, 0.5)
    music[i0:i0 + nb] += 0.16 * pad
    if lvl >= 1:
        # basse en croches
        for k in range(8):
            j = i0 + int(k * beat / 2 * SR); m = int(beat / 2 * SR * 0.9)
            if j + m > N: break
            bs = saw(note(root - 12), m, 0.002)
            music[j:j + m] += 0.22 * lp_fast(bs, 500) * env_adsr(m, 0.005, 0.08, 0.6, 0.05)
        # arpège
        for k in range(16):
            j = i0 + int(k * beat / 4 * SR); m = int(beat / 4 * SR * 0.8)
            if j + m > N: break
            n = chord[k % 3] + 24
            ar = np.sign(np.sin(2 * np.pi * note(n) * np.arange(m) / SR))
            music[j:j + m] += 0.035 * lp_fast(ar, 3000) * env_adsr(m, 0.002, 0.05, 0.3, 0.05)
    if lvl >= 1:
        for k in range(4):   # batterie
            j = i0 + int(k * beat * SR)
            m = int(0.35 * SR)
            if j + m > N: break
            tt = np.arange(m) / SR
            kick = np.sin(2 * np.pi * (45 + 90 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9)
            music[j:j + m] += 0.45 * kick
            if k in (1, 3):
                sn = rng.standard_normal(m) * np.exp(-tt * 18) * 0.5 + np.sin(2 * np.pi * 190 * tt) * np.exp(-tt * 25) * 0.3
                music[j:j + m] += 0.22 * sn
            for hh in (0, 0.5) if lvl < 2 else (0, 0.25, 0.5, 0.75):
                jh = j + int(hh * beat * SR); mh = int(0.05 * SR)
                if jh + mh > N: break
                music[jh:jh + mh] += 0.05 * rng.standard_normal(mh) * np.exp(-np.arange(mh) / SR * 80)

# ------------------------------------------------------------------ moteurs
engines = np.zeros(N)
C = 343.0
for sh in timeline["shots"]:
    tp = sh.get("traj")
    if not tp or not os.path.exists(tp): continue
    tr = json.load(open(tp)); fps = tr["fps"]; nf = tr["frames"]
    cam = np.array(tr["cam"][:2])
    i0 = int(sh["start"] * SR); n = int(sh["dur"] * SR)
    if i0 + n > N: n = N - i0
    tt = np.arange(n) / SR
    for cname, pts in tr["cars"].items():
        P = np.array(pts)                                    # (nf, 2)
        fidx = np.clip(tt * fps, 0, nf - 1)
        x = np.interp(fidx, np.arange(nf), P[:, 0]); y = np.interp(fidx, np.arange(nf), P[:, 1])
        d = np.hypot(x - cam[0], y - cam[1]) + 1.0
        vx = np.gradient(x) * SR; vy = np.gradient(y) * SR
        speed = np.hypot(vx, vy)
        vr = np.gradient(d) * SR                              # vitesse radiale
        dop = C / (C + vr)
        base = {"red": 1.0, "black": 0.82, "pearl": 1.15}.get(cname, 1.0)
        rpm_f = base * (38 + 2.2 * speed) * dop               # fondamentale (Hz)
        ph = 2 * np.pi * np.cumsum(rpm_f) / SR
        tone = (np.sin(ph) + 0.6 * np.sin(2 * ph + 0.3) + 0.35 * np.sin(3 * ph) + 0.2 * np.sin(4.5 * ph)) / 2.2
        rough = 1 + 0.25 * np.sin(ph * 0.5)
        noise = lp_fast(rng.standard_normal(n), 900) * np.clip(speed / 40, 0, 1)
        sig = tone * rough * (0.6 + 0.4 * np.clip(speed / 30, 0, 1)) + 0.5 * noise
        gain = np.clip(6.0 / d, 0, 1.2)
        engines[i0:i0 + n] += 0.5 * sig * gain

# ------------------------------------------------------------------ mixage
fade = np.ones(N); fi = int(2 * SR); fo = int(4 * SR)
fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] = np.linspace(1, 0, fo)
mix = (0.7 * music + 0.55 * engines) * fade
mix = np.tanh(mix * 1.2) * 0.9
stereo = np.stack([mix, np.roll(mix, 30)], axis=1)
pcm = (np.clip(stereo, -1, 1) * 32000).astype(np.int16)
with wave.open(OUT, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("audio ok", OUT, TOTAL, "s")
