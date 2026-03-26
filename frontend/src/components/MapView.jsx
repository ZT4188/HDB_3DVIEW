import React, { useEffect, useState, useCallback } from 'react'
import DeckGL from '@deck.gl/react'
import { ScenegraphLayer, SimpleMeshLayer } from '@deck.gl/mesh-layers'
import { GeoJsonLayer } from '@deck.gl/layers'
import { Map } from 'react-map-gl/mapbox'
import 'mapbox-gl/dist/mapbox-gl.css'
import { useSimStore } from '../store/simStore.js'
import { occupancyColor, DEFAULT_COLOR } from '../utils/colorScale.js'
import { api } from '../utils/api.js'

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN
const SINGAPORE_CENTER = { longitude: 103.8198, latitude: 1.3521, zoom: 11 }

// Fallback: extruded box geometry for buildings without 3D models
const BOX_MESH = {
  positions: new Float32Array([
    -0.5,-0.5,0, 0.5,-0.5,0, 0.5,0.5,0, -0.5,0.5,0,
    -0.5,-0.5,1, 0.5,-0.5,1, 0.5,0.5,1, -0.5,0.5,1,
  ]),
  indices: { value: new Uint16Array([0,1,2,0,2,3, 4,5,6,4,6,7, 0,1,5,0,5,4, 2,3,7,2,7,6, 1,2,6,1,6,5, 0,3,7,0,7,4]), size: 1 },
  normals: new Float32Array(24).fill(0),
}

export default function MapView() {
  const [viewState, setViewState] = useState({
    ...SINGAPORE_CENTER,
    pitch: 45,
    bearing: 0,
  })
  const [boundaryData, setBoundaryData] = useState(null)

  const {
    buildings, setBuildings,
    residentMap, setSelectedBuilding,
    activeSession,
  } = useSimStore()

  // Load buildings GeoJSON
  useEffect(() => {
    api.buildings.list().then((geojson) => {
      setBuildings(geojson.features || [])
    }).catch(console.error)
  }, [])

  // Load Singapore boundary
  useEffect(() => {
    fetch('/assets/singapore-boundary.geojson')
      .then((r) => r.json())
      .then(setBoundaryData)
      .catch(() => {
        // Fallback: fetch from CDN if local asset unavailable
        fetch('https://raw.githubusercontent.com/yinshanyang/singapore/master/maps/0-country.geojson')
          .then((r) => r.json())
          .then(setBoundaryData)
          .catch(console.error)
      })
  }, [])

  const handleBuildingClick = useCallback(({ object }) => {
    if (!object) return
    api.buildings.get(object.properties?.id || object.id)
      .then(setSelectedBuilding)
      .catch(console.error)
  }, [])

  // ── Build layers ─────────────────────────────────────────
  const layers = []

  // 1. Singapore island boundary
  if (boundaryData) {
    layers.push(new GeoJsonLayer({
      id: 'singapore-boundary',
      data: boundaryData,
      filled: true,
      stroked: true,
      getFillColor: [34, 197, 94, 30],
      getLineColor: [34, 197, 94, 180],
      getLineWidth: 200,
      pickable: false,
    }))
  }

  // 2. HDB buildings — extruded boxes coloured by occupancy
  if (buildings.length > 0) {
    layers.push(new SimpleMeshLayer({
      id: 'hdb-buildings',
      data: buildings,
      mesh: BOX_MESH,
      getPosition: (f) => [
        f.geometry.coordinates[0],
        f.geometry.coordinates[1],
        0,
      ],
      getScale: (f) => {
        const units = f.properties.dwelling_units || 1
        const floors = Math.max(3, Math.round(units / 4))
        return [30, 30, floors * 3]
      },
      getColor: (f) => {
        const id = f.properties?.id
        const residents = residentMap[id]
        if (residents == null) return DEFAULT_COLOR
        const capacity = (f.properties.dwelling_units || 1) * 3
        return occupancyColor(residents / capacity)
      },
      material: {
        ambient: 0.4,
        diffuse: 0.6,
        shininess: 32,
      },
      pickable: true,
      onClick: handleBuildingClick,
      updateTriggers: {
        getColor: [residentMap],
      },
    }))
  }

  return (
    <DeckGL
      viewState={viewState}
      onViewStateChange={({ viewState }) => setViewState(viewState)}
      controller={{ touchRotate: true, dragRotate: true }}
      layers={layers}
      style={{ position: 'absolute', inset: 0 }}
      getCursor={({ isHovering }) => isHovering ? 'pointer' : 'grab'}
    >
      <Map
        mapboxAccessToken={MAPBOX_TOKEN}
        mapStyle="mapbox://styles/mapbox/dark-v11"
        reuseMaps
      />
    </DeckGL>
  )
}
