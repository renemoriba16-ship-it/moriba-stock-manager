#!/bin/bash
# Rend tous les plans du film, avec reprise après interruption.
cd "$(dirname "$0")"
BLENDER_PY="${BLENDER_PY:-python}"   # python avec le module bpy, ou: blender -b -P
SHOTS=$($BLENDER_PY film.py -- --list | awk '/^[A-Z][0-9]/{print $1}')
for s in $SHOTS; do
  d="renders/shots/$s"
  mkdir -p "$d"
  find "$d" -maxdepth 1 -name 'f_*.png' -size 0 -delete   # images interrompues
  echo "=== $s $(date +%H:%M:%S)"
  $BLENDER_PY film.py -- --shot "$s" > "$d/render.log" 2>&1 || echo "FAILED $s"
done
echo ALL_DONE
