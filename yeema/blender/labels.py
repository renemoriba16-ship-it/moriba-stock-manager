# Generates label textures for yeema products with PIL
import sys
from PIL import Image, ImageDraw, ImageFont
S = sys.argv[1]
F = S + "/fonts/Fraunces.ttf"; I = S + "/fonts/Inter.ttf"

def font(path, size, wght=None, opsz=None):
    f = ImageFont.truetype(path, size)
    try:
        axes = f.get_variation_axes()
        vals = []
        for a in axes:
            n = a['name'] if isinstance(a['name'], str) else a['name'].decode()
            if n.lower().startswith('weight') and wght: vals.append(wght)
            elif n.lower().startswith('optical') and opsz: vals.append(opsz)
            else: vals.append(a['default'])
        f.set_variation_by_axes(vals)
    except Exception as e:
        print("var font", e)
    return f

def label(name, sub, vol, out, bg=(226, 212, 192), ink=(43, 29, 20), accent=(176, 112, 52), W=2048, H=820, logo=1.0):
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    cx = W // 2  # front of label at u=0.5
    k = H/820
    big = font(F, int(330*k*logo), wght=380, opsz=144)
    d.text((cx, H*0.36), "yeema", font=big, fill=ink, anchor="mm")
    small = font(I, int(40*k), wght=500)
    d.text((cx, H*0.70), name, font=small, fill=ink, anchor="mm")
    tiny = font(I, int(28*k), wght=400)
    d.text((cx, H*0.80), sub, font=tiny, fill=accent, anchor="mm")
    d.text((cx, H*0.90), vol, font=tiny, fill=ink, anchor="mm")
    d.line([(cx-120*k, H*0.58), (cx+120*k, H*0.58)], fill=accent, width=3)
    # back text
    for i, t in enumerate(["Formulé avec soin.", "Huiles de baobab, karité & ricin.", "Pour cheveux bouclés, frisés, crépus."]):
        d.text((cx-W*0.32, H*0.35 + i*55*k), t, font=tiny, fill=ink, anchor="lm")
        d.text((cx+W*0.32, H*0.35 + i*55*k), t, font=tiny, fill=ink, anchor="rm")
    im.save(out)

label("HUILE NOURRISSANTE", "BAOBAB · KARITÉ · RICIN", "30 ml — 1.0 fl oz", S+"/tex/label_oil.png", W=2816, H=640)
label("SHAMPOING DOUCEUR", "AVOCAT · ALOE VERA", "250 ml — 8.4 fl oz", S+"/tex/label_shampoo.png", W=2048, H=1010, logo=0.62)
label("MASQUE RÉPARATEUR", "MANGUE · BEURRE DE CACAO", "200 ml — 6.7 fl oz", S+"/tex/label_mask.png", W=4200, H=520)
print("ok")
