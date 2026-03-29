import React, { useEffect, useRef } from 'react'
import { Deck } from '@deck.gl/core'
import { SimpleMeshLayer } from '@deck.gl/mesh-layers'
import { GeoJsonLayer } from '@deck.gl/layers'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import { useSimStore } from '../store/simStore.js'
import { occupancyColor, DEFAULT_COLOR } from '../utils/colorScale.js'
import { api } from '../utils/api.js'

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN

const BOX_MESH = {
  positions: new Float32Array([
    -0.5,-0.5,0, 0.5,-0.5,0, 0.5,0.5,0, -0.5,0.5,0,
    -0.5,-0.5,1, 0.5,-0.5,1, 0.5,0.5,1, -0.5,0.5,1,
  ]),
  indices: { value: new Uint16Array([0,1,2,0,2,3,4,5,6,4,6,7,0,1,5,0,5,4,2,3,7,2,7,6,1,2,6,1,6,5,0,3,7,0,7,4]), size: 1 },
  normals: new Float32Array(24).fill(0),
}

export default function MapView() {
  const mapContainer = useRef(null)
  const deckCanvas = useRef(null)
  const mapRef = useRef(null)
  const deckRef = useRef(null)

  const { buildings, setBuildings, residentMap, setSelectedBuilding } = useSimStore()

  // Init map + deck
  useEffect(() => {
    mapboxgl.accessToken = MAPBOX_TOKEN

    const map = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [103.8198, 1.3521],
      zoom: 11,
      pitch: 45,
      bearing: 0,
      antialias: true,
    })
    mapRef.current = map

    const deck = new Deck({
      canvas: deckCanvas.current,
      width: '100%',
      height: '100%',
      initialViewState: {
        longitude: 103.8198,
        latitude: 1.3521,
        zoom: 11,
        pitch: 45,
        bearing: 0,
      },
      controller: true,
      layers: [],
      onViewStateChange: ({ viewState }) => {
        map.jumpTo({
          center: [viewState.longitude, viewState.latitude],
          zoom: viewState.zoom,
          bearing: viewState.bearing,
          pitch: viewState.pitch,
        })
      },
    })
    deckRef.current = deck

    // Sync map drag → deck
    map.on('move', () => {
      const c = map.getCenter()
      deck.setProps({
        viewState: {
          longitude: c.lng,
          latitude: c.lat,
          zoom: map.getZoom(),
          bearing: map.getBearing(),
          pitch: map.getPitch(),
        },
      })
    })

    // Singapore boundary
    map.on('load', () => {
      fetch('https://raw.githubusercontent.com/yinshanyang/singapore/master/maps/0-country.geojson')
        .then(r => r.json())
        .then(geojson => {
          map.addSource('sg', { type: 'geojson', data: geojson })
          map.addLayer({ id: 'sg-fill', type: 'fill', source: 'sg', paint: { 'fill-color': '#22c55e', 'fill-opacity': 0.08 } })
          map.addLayer({ id: 'sg-line', type: 'line', source: 'sg', paint: { 'line-color': '#22c55e', 'line-width': 1.5 } })
        })
        .catch(console.error)
    })

    return () => { deck.finalize(); map.remove() }
  }, [])

  // Update deck layers
  useEffect(() => {
    if (!deckRef.current || buildings.length === 0) return

    deckRef.current.setProps({
      layers: [
        new SimpleMeshLayer({
          id: 'hdb-buildings',
          data: buildings,
          mesh: BOX_MESH,
          getPosition: f => [f.geometry.coordinates[0], f.geometry.coordinates[1], 0],
          getScale: f => {
            const floors = Math.max(3, Math.round((f.properties.dwelling_units || 4) / 4))
            return [30, 30, floors * 3]
          },
          getColor: f => {
            const residents = residentMap[f.properties?.id]
            if (residents == null) return DEFAULT_COLOR
            const capacity = (f.properties.dwelling_units || 1) * 3
            return occupancyColor(residents / capacity)
          },
          pickable: true,
          onClick: ({ object }) => {
            if (!object) return
            api.buildings.get(object.properties?.id).then(setSelectedBuilding).catch(console.error)
          },
          updateTriggers: { getColor: [residentMap] },
        }),
      ],
    })
  }, [buildings, residentMap])

  // Load buildings data
  useEffect(() => {
    api.buildings.list().then(g => setBuildings(g.features || [])).catch(console.error)
  }, [])

  return (
    <div style={{ position: 'absolute', inset: 0 }}>
      {/* Mapbox basemap */}
      <div ref={mapContainer} style={{ position: 'absolute', inset: 0 }} />
      {/* deck.gl canvas on top, pointer-events none so map handles pan/zoom */}
      <canvas
        ref={deckCanvas}
        style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}
      />
    </div>
  )
}