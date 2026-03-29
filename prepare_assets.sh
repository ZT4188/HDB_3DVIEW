#!/usr/bin/env bash
# prepare_assets.sh
# Downloads HDB 3D data and converts CityJSON to glTF for deck.gl rendering.
# Run this once before starting the application.

set -e

ASSETS_DIR="$(dirname "$0")/../assets"
mkdir -p "$ASSETS_DIR"

echo "📦 Downloading HDB 3D data from ualsg/hdb3d-data..."

# Download hdb.json (unit counts)
if [ ! -f "$ASSETS_DIR/hdb.json" ]; then
  curl -L \
    "https://raw.githubusercontent.com/ualsg/hdb3d-data/master/data/hdb.json" \
    -o "$ASSETS_DIR/hdb.json"
  echo "✅ hdb.json downloaded"
else
  echo "⏭️  hdb.json already exists, skipping"
fi

# Download CityJSON 3D models
if [ ! -f "$ASSETS_DIR/hdb3d-cityjson.json" ]; then
  echo "📥 Downloading CityJSON models (this may take a moment)..."
  curl -L \
    "https://github.com/ualsg/hdb3d-data/raw/master/data/hdb3d-r.json" \
    -o "$ASSETS_DIR/hdb3d-cityjson.json"
  echo "✅ CityJSON downloaded"
else
  echo "⏭️  CityJSON already exists, skipping"
fi

# Download Singapore boundary GeoJSON
if [ ! -f "$ASSETS_DIR/singapore-boundary.geojson" ]; then
  echo "📥 Downloading Singapore boundary..."
  curl -L \
    "https://raw.githubusercontent.com/yinshanyang/singapore/master/maps/0-country.geojson" \
    -o "$ASSETS_DIR/singapore-boundary.geojson"
  echo "✅ Singapore boundary downloaded"
fi

echo ""
echo "🔄 Converting CityJSON → glTF..."
echo "   (Requires: pip install cjio)"

if command -v cjio &>/dev/null; then
  cjio "$ASSETS_DIR/hdb3d-cityjson.json" \
    lod_filter 1 \
    export "$ASSETS_DIR/hdb3d.glb"
  echo "✅ glTF exported to assets/hdb3d.glb"
else
  echo "⚠️  cjio not found. Install with: pip install cjio"
  echo "   Then re-run: cjio assets/hdb3d-cityjson.json lod_filter 1 export assets/hdb3d.glb"
  echo ""
  echo "   Alternatively, the frontend will fall back to extruded polygon rendering."
fi

echo ""
echo "✅ Asset preparation complete. Run: docker compose up --build"