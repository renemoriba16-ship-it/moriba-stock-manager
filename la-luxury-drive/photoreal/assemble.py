"""
Montage final : plans -> clips (bandes cinéma 2.39:1, étalonnage, titres),
fondus entre les actes, générique, bande son.
Usage : python assemble.py   (avec le python qui a bpy, pour lire la liste des plans)
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
SHOTS_DIR = os.path.join(HERE, "renders", "shots")
TMP = os.path.join(HERE, "renders", "edit"); os.makedirs(TMP, exist_ok=True)
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Light.otf"
FONT_B = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"
for f in (FONT, FONT_B):
    if not os.path.exists(f):
        FONT = FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FPS = 24
W, H = 1280, 720
BAR = 88   # hauteur des bandes noires (1280x544 visibles ≈ 2.35:1)

lst = subprocess.run([PY, os.path.join(HERE, "film.py"), "--", "--list"], capture_output=True, text=True).stdout
shots = []
for line in lst.splitlines():
    p = line.split()
    if p and p[0][0].isalpha() and p[0][1:].isdigit():
        shots.append(dict(name=p[0], loc=p[1], dur=int(p[2].rstrip("s")), hold=("hold=True" in line)))

TITLES = {
    "C01": [("L'HEURE DORÉE", 64, FONT_B, 0.8, 5.6), ("un film en quatre actes", 26, FONT, 1.6, 5.6)],
    "C02": [("I.  LA CÔTE", 30, FONT, 0.3, 3.5)],
    "D01": [("II.  LE DÉSERT", 44, FONT_B, 0.6, 4.6)],
    "T01": [("III.  LE CIRCUIT", 44, FONT_B, 0.6, 5.4)],
    "T10": [("VICTOIRE", 40, FONT_B, 1.0, 4.6)],
    "Y01": [("IV.  LE DERNIER RAYON", 44, FONT_B, 0.6, 5.4)],
    "Y05": [("FIN", 56, FONT_B, 2.5, 7.6)],
}
ACT_FIRST = {"C01", "D01", "T01", "Y01"}
ACT_LAST = {"C10", "D08", "T10", "Y05"}

def esc(t):
    return t.replace("\\", "\\\\").replace("'", "’").replace(":", "\\:")

def text_filters(name):
    out = []
    for i, (txt, size, font, t0, t1) in enumerate(TITLES.get(name, [])):
        y = f"(h/2-{size})" if i == 0 else "(h/2+30)"
        a = f"if(lt(t,{t0}),0,if(lt(t,{t0}+0.8),(t-{t0})/0.8,if(lt(t,{t1}-0.8),1,max(0,({t1}-t)/0.8))))"
        out.append(f"drawtext=fontfile={font}:text='{esc(txt)}':fontsize={size}:fontcolor=white:alpha='{a}':x=(w-text_w)/2:y={y}:shadowcolor=black@0.5:shadowx=2:shadowy=2")
    return out

PREVIEW = "--preview" in sys.argv
if PREVIEW:
    done = []
    for sh in shots:
        d = os.path.join(SHOTS_DIR, sh["name"])
        ok = os.path.exists(os.path.join(d, "hold.png")) if sh["hold"] else \
            len([f for f in os.listdir(d) if f.startswith("f_") and os.path.getsize(os.path.join(d, f)) > 0]) >= sh["dur"] * FPS if os.path.isdir(d) else False
        if not ok: break
        done.append(sh)
    shots = done
    print("preview shots:", [s["name"] for s in shots])

timeline = dict(shots=[], acts=[], total=0)
clips = []
t = 0.0
cur_act = None
for sh in shots:
    name, dur = sh["name"], sh["dur"]
    d = os.path.join(SHOTS_DIR, name)
    nf = dur * FPS
    grade = "eq=contrast=1.04:saturation=1.06,vignette=angle=PI/5"
    vf = [grade]
    if sh["hold"]:
        src = ["-loop", "1", "-framerate", str(FPS), "-t", str(dur), "-i", os.path.join(d, "hold.png")]
        # lent travelling avant (Ken Burns) sur les plans fixes
        vf.insert(0, f"scale={W*2}:{H*2},zoompan=z='1+0.05*on/{nf}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}")
    else:
        src = ["-framerate", str(FPS), "-i", os.path.join(d, "f_%04d.png")]
        vf.insert(0, f"scale={W}:{H}:flags=lanczos")
    vf += [f"drawbox=x=0:y=0:w=iw:h={BAR}:color=black:t=fill", f"drawbox=x=0:y=ih-{BAR}:w=iw:h={BAR}:color=black:t=fill"]
    vf += text_filters(name)
    if name in ACT_FIRST: vf.append("fade=t=in:st=0:d=0.8")
    if name in ACT_LAST: vf.append(f"fade=t=out:st={dur-0.8}:d=0.8")
    out = os.path.join(TMP, f"{name}.mp4")
    cmd = ["ffmpeg", "-loglevel", "error", "-y", *src, "-vf", ",".join(vf), "-frames:v", str(nf),
           "-r", str(FPS), "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", out]
    subprocess.run(cmd, check=True)
    clips.append(out)
    timeline["shots"].append(dict(name=name, start=t, dur=dur, traj=os.path.join(d, "traj.json")))
    if sh["loc"] != cur_act:
        if timeline["acts"]: timeline["acts"][-1][1] = t
        timeline["acts"].append([t, None, sh["loc"]]); cur_act = sh["loc"]
    t += dur
    print("clip", name, flush=True)

# générique de fin
CRED = 4
cred_out = os.path.join(TMP, "ZZ_credits.mp4")
lines = ["Scénario, mise en scène et rendu : Blender (Cycles)",
         "Panoramas HDRI : Poly Haven (CC0)  •  Voiture : Khronos CarConcept (base CC0)",
         "Musique et sons : synthèse originale"]
dt = ",".join(f"drawtext=fontfile={FONT}:text='{esc(l)}':fontsize=22:fontcolor=white@0.85:x=(w-text_w)/2:y=h/2-50+{i*40}" for i, l in enumerate(lines))
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r={FPS}:d={CRED}",
                "-vf", dt + ",fade=t=in:st=0:d=0.6,fade=t=out:st=3.2:d=0.8", "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", cred_out], check=True)
clips.append(cred_out)
timeline["acts"][-1][1] = t
t += CRED
timeline["total"] = t
json.dump(timeline, open(os.path.join(TMP, "timeline.json"), "w"), indent=1)

with open(os.path.join(TMP, "list.txt"), "w") as f:
    for c in clips: f.write(f"file '{c}'\n")
video = os.path.join(TMP, "video.mp4")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(TMP, "list.txt"), "-c", "copy", video], check=True)

wav = os.path.join(TMP, "audio.wav")
subprocess.run([PY, os.path.join(HERE, "make_audio.py"), os.path.join(TMP, "timeline.json"), wav], check=True)
final = os.path.join(HERE, "renders", "apercu_partiel.mp4" if PREVIEW else "L_Heure_Doree.mp4")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", video, "-i", wav, "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", final], check=True)
print("FINAL", final, t, "s")
