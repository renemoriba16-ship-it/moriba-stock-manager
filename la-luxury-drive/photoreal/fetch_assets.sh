#!/bin/sh
# Télécharge les ressources gratuites utilisées par la scène
set -e
cd "$(dirname "$0")" && mkdir -p assets
curl -L -o assets/victoria_sunset_4k.hdr https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/4k/victoria_sunset_4k.hdr   # Poly Haven, CC0
curl -L -o assets/CarConcept.glb https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/CarConcept/glTF-Binary/CarConcept.glb  # Khronos, base CC0
