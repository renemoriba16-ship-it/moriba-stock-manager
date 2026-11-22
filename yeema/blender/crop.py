import sys
from PIL import Image
S, R = sys.argv[1], sys.argv[2]
for n in ["oil", "shampoo", "mask"]:
    im = Image.open(f"{S}/render/products/{n}.png").convert("RGBA")
    a = im.getchannel("A").point(lambda v: 255 if v > 120 else 0)
    x0, y0, x1, y1 = a.getbbox()
    w, h = x1 - x0, y1 - y0
    # target 4:5 canvas, product fills ~62% of height (wide jar limited by width)
    W, H = 900, 1125
    scale = min(H * 0.62 / h, W * 0.70 / w)
    pad = 120  # keep soft shadow around the object
    crop = im.crop((max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad)))
    crop = crop.resize((int(crop.width * scale), int(crop.height * scale)), Image.LANCZOS)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ox = (W - crop.width) // 2
    oy = int(H * 0.86 - (y1 - max(0, y0 - pad)) * scale)  # base of product at 86% height
    out.alpha_composite(crop, (ox, oy)) if ox >= 0 and oy >= 0 else out.paste(crop, (ox, oy), crop)
    # feather edges so the soft shadow never shows a hard crop line
    from PIL import ImageDraw, ImageFilter, ImageChops
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rectangle((70, 40, W-70, H-50), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(45))
    out.putalpha(ImageChops.multiply(out.getchannel("A"), m))
    out.save(f"{R}/products/{n}.webp", quality=86, method=5)
print("cropped")
