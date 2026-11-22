#!/bin/sh
set -e
S=/tmp/claude-0/-home-user-moriba-stock-manager/425a1ee1-386f-5283-a191-1d1af629f46f/scratchpad
R=/home/user/moriba-stock-manager/yeema/assets
for f in $S/render/hero/f_*.png; do b=$(basename $f .png); [ -f $R/hero/$b.webp ] || ffmpeg -loglevel error -y -i $f -c:v libwebp -quality 78 -compression_level 5 $R/hero/$b.webp; done
for n in oil shampoo mask group; do [ -f $S/render/products/$n.png ] && ffmpeg -loglevel error -y -i $S/render/products/$n.png -c:v libwebp -quality 85 $R/products/$n.webp; done
if [ -f $S/render/blob/b_0096.jpg ]; then
  ffmpeg -loglevel error -y -framerate 24 -i $S/render/blob/b_%04d.jpg -vf scale=800:800 -c:v libx264 -pix_fmt yuv420p -crf 23 -movflags +faststart -an $R/oil-loop.mp4
  ffmpeg -loglevel error -y -i $S/render/blob/b_0001.jpg -vf scale=800:800 -q:v 4 $R/oil-loop.jpg
fi
du -sh $R
