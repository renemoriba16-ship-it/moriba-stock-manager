"""
Prépare les textures 3D à partir des photos des maillots (fond blanc).

    pip install numpy opencv-python-headless pillow
    python blender/textures.py

Pour chaque photo de site/images/ listée dans JERSEYS :
 1. détourage (le fond blanc est retiré par remplissage depuis les bords)
 2. silhouette moyenne de tous les maillots -> blender/silhouette.json
    (le script Blender maillot.py construit le modèle 3D avec cette forme)
 3. texture 2048x1024 : face (photo recadrée sur le maillot, bords prolongés)
    + dos (couleurs et rayures reprises de la face, sans les logos)
    -> site/models/tex/<id>.webp
"""
import json
import os

import cv2
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
IMG = os.path.join(ROOT, "site", "images")
OUT = os.path.join(ROOT, "site", "models", "tex")
SIL = os.path.join(ROOT, "blender", "silhouette.json")

# id produit (config.js) -> photo (fond blanc)
JERSEYS = {
    "fra-dom": "france-domicile",
    "fra-ext": "france-exterieur",
    "ang-dom": "angleterre-domicile",
    "ang-ext": "angleterre-exterieur",
    "bel-dom": "belgique-domicile",
    "psg-dom": "psg-domicile",
    "bar-dom": "barcelone-domicile",
    "rma-3rd": "real-madrid-third",
    "mun-dom": "manchester-united-domicile",
    "che-dom": "chelsea-domicile",
    "bay-dom": "bayern-domicile",
}
FACE = 1024  # taille d'une moitié de texture


def cutout(rgb):
    """Masque du maillot : remplissage du fond depuis les bords."""
    h, w = rgb.shape[:2]
    img = cv2.GaussianBlur(rgb, (3, 3), 0)
    bg = np.median(np.concatenate([img[0], img[-1], img[:, 0], img[:, -1]]), axis=0)
    diff = np.abs(img.astype(np.int16) - bg.astype(np.int16)).max(axis=2)
    near = (diff < 14).astype(np.uint8)
    flood = np.zeros((h + 2, w + 2), np.uint8)
    region = near.copy()
    for (x, y) in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]:
        if near[y, x]:
            cv2.floodFill(region, flood, (x, y), 2)
    mask = (region != 2).astype(np.uint8)
    # garder la plus grande forme, boucher les trous
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    if n > 1:
        biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        mask = (lab == biggest).astype(np.uint8)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    full = np.zeros_like(mask)
    cv2.drawContours(full, cnts, -1, 1, thickness=cv2.FILLED)
    full = cv2.morphologyEx(full, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    return full


def load(name):
    im = Image.open(os.path.join(IMG, name + ".webp")).convert("RGB")
    return np.array(im)


def main():
    os.makedirs(OUT, exist_ok=True)
    data = {}
    for pid, name in JERSEYS.items():
        rgb = load(name)
        m = cutout(rgb)
        ys, xs = np.where(m > 0)
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        data[pid] = (rgb[y0:y1, x0:x1], m[y0:y1, x0:x1])

    # ---- silhouette moyenne (symétrique), dans un carré normalisé
    S = 256
    acc = np.zeros((S, S), np.float32)
    aspects = []
    for rgb, m in data.values():
        aspects.append(m.shape[1] / m.shape[0])
        r = cv2.resize(m.astype(np.float32), (S, S), interpolation=cv2.INTER_AREA)
        acc += r + r[:, ::-1]
    acc /= 2 * len(data)
    mean = (acc > 0.5).astype(np.uint8)
    cnts, _ = cv2.findContours(mean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cnts, key=cv2.contourArea)
    c = cv2.approxPolyDP(c, 1.2, True)[:, 0, :].astype(float)
    aspect = float(np.mean(aspects))
    height = 1.54
    width = height * aspect
    pts = [((x / (S - 1) - 0.5) * width, (0.5 - y / (S - 1)) * height) for x, y in c]
    json.dump({"aspect": aspect, "width": width, "height": height, "outline": pts}, open(SIL, "w"), indent=1)
    print(f"silhouette : {len(pts)} points, rapport largeur/hauteur {aspect:.3f}")

    # ---- textures
    for pid, (rgb, m) in data.items():
        face = cv2.resize(rgb, (FACE, FACE), interpolation=cv2.INTER_AREA)
        fm = cv2.resize(m * 255, (FACE, FACE), interpolation=cv2.INTER_LINEAR)
        inside = fm > 127
        # prolonger les couleurs du maillot au-delà du bord (évite le blanc sur les bords du modèle)
        small = cv2.resize(face, (256, 256), interpolation=cv2.INTER_AREA)
        sm = cv2.resize(fm, (256, 256), interpolation=cv2.INTER_AREA) > 160
        filled = cv2.inpaint(small, (~sm).astype(np.uint8) * 255, 9, cv2.INPAINT_TELEA)
        filled = cv2.resize(filled, (FACE, FACE), interpolation=cv2.INTER_CUBIC)
        alpha = cv2.GaussianBlur((fm > 127).astype(np.float32), (0, 0), 1.2)[..., None]
        front = (face * alpha + filled * (1 - alpha)).astype(np.uint8)

        # dos : pour chaque colonne, couleur médiane du torse (garde les rayures, efface les logos)
        torso = slice(int(FACE * 0.30), int(FACE * 0.92))
        cols = np.zeros((FACE, 3), np.float32)
        last = np.median(front[torso].reshape(-1, 3), axis=0)
        for x in range(FACE):
            colpx = front[torso, x][inside[torso, x]]
            if len(colpx) > 20:
                last = np.median(colpx, axis=0)
            cols[x] = last
        cols = cv2.GaussianBlur(cols[None], (0, 0), 1.5)[0]
        back = np.repeat(cols[None, ::-1], FACE, axis=0)
        # garder col / bas d'origine (bandes du haut et du bas, retournées)
        top = int(FACE * 0.12)
        back[:top] = front[:top, ::-1]
        # légère variation de lumière verticale du tissu
        shade = np.linspace(1.04, 0.94, FACE)[:, None, None]
        back = np.clip(back * shade, 0, 255).astype(np.uint8)

        tex = np.concatenate([front, back], axis=1)
        Image.fromarray(tex).resize((1536, 768), Image.LANCZOS).save(os.path.join(OUT, pid + ".webp"), "WEBP", quality=84, method=6)
        print("texture", pid)


if __name__ == "__main__":
    main()
