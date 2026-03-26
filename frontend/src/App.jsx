import React, { useEffect } from 'react'
import MapView from './components/MapView.jsx'
import InfoPanel from './components/InfoPanel.jsx'
import StatsPanel from './components/StatsPanel.jsx'
import SimControls from './components/SimControls.jsx'
import SessionModal from './components/SessionModal.jsx'
import Timeline from './components/Timeline.jsx'
import { useSimStore } from './store/simStore.js'
import { useWebSocket } from './hooks/useWebSocket.js'

export default function App() {
  const { activeSession } = useSimStore()
  useWebSocket(activeSession?.id)

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      {/* Full-screen 3D map */}
      <MapView />

      {/* Left: building info panel (visible when building selected) */}
      <InfoPanel />

      {/* Right: simulation stats + move log */}
      <StatsPanel />

      {/* Bottom: simulation controls + timeline */}
      <SimControls />
      <Timeline />

      {/* Session management modal */}
      <SessionModal />
    </div>
  )
}
