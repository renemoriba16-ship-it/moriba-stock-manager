import sys
from PIL import Image
for path, out, pad in [(a.split(':')[0], a.split(':')[1], float(a.split(':')[2])) for a in sys.argv[1:]]:
    im = Image.open(path).convert("RGBA")
    x0, y0, x1, y1 = im.getchannel("A").point(lambda v: 255 if v > 10 else 0).getbbox()
    p = int(pad*max(x1-x0, y1-y0))
    im = im.crop((max(0, x0-p), max(0, y0-p), min(im.width, x1+p), min(im.height, y1)))  # no pad at the bottom: plants stand on the edge
    im.save(out, quality=84, method=5); print(out, im.size)
