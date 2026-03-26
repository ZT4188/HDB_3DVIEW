import React, { useState } from 'react'
import { useSimStore } from '../store/simStore.js'
import { api } from '../utils/api.js'

const s = {
  bar: {
    position: 'absolute',
    bottom: 60,
    left: '50%',
    transform: 'translateX(-50%)',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    background: 'rgba(17,19,24,0.95)',
    border: '1px solid #242830',
    borderRadius: 40,
    padding: '8px 14px',
    backdropFilter: 'blur(12px)',
    fontFamily: "'DM Mono', monospace",
  },
  btn: {
    background: 'none',
    border: '1px solid #242830',
    borderRadius: 20,
    color: '#e8ecf0',
    cursor: 'pointer',
    fontSize: 12,
    padding: '7px 16px',
    letterSpacing: '0.05em',
    transition: 'all 0.15s',
    whiteSpace: 'nowrap',
  },
  btnPrimary: {
    background: '#00e5a0',
    border: '1px solid #00e5a0',
    color: '#0a0c10',
    fontWeight: 600,
  },
  btnDanger: {
    border: '1px solid #374151',
    color: '#9ca3af',
  },
  divider: {
    width: 1,
    height: 24,
    background: '#242830',
    margin: '0 4px',
  },
  sessionName: {
    fontSize: 11,
    color: '#6b7280',
    padding: '0 8px',
    maxWidth: 140,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
}

export default function SimControls() {
  const {
    activeSession, setActiveSession,
    simStatus, setSimStatus,
    setShowSessionModal,
    setResidentMap,
    setTimelineYear,
  } = useSimStore()
  const [loading, setLoading] = useState(false)

  const handleAssign = async () => {
    if (!activeSession) return
    setLoading(true)
    try {
      const result = await api.sessions.assign(activeSession.id)
      // Reset resident map to initial assignment
      setResidentMap({})
      setTimelineYear(null)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleStart = async () => {
    if (!activeSession) return
    setLoading(true)
    try {
      await api.sessions.start(activeSession.id)
      setSimStatus('running')
      setTimelineYear(null) // Switch to live mode
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handlePause = async () => {
    if (!activeSession) return
    try {
      await api.sessions.pause(activeSession.id)
      setSimStatus('paused')
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <div style={s.bar}>
      {/* Session selector */}
      <button
        style={s.btn}
        onClick={() => setShowSessionModal(true)}
      >
        {activeSession ? '⊞ Sessions' : '+ New Session'}
      </button>

      {activeSession && (
        <>
          <span style={s.sessionName}>{activeSession.name}</span>
          <div style={s.divider} />

          <button
            style={{ ...s.btn, ...s.btnDanger }}
            onClick={handleAssign}
            disabled={loading || simStatus === 'running'}
          >
            ⟳ Assign
          </button>

          {simStatus !== 'running' ? (
            <button
              style={{ ...s.btn, ...s.btnPrimary }}
              onClick={handleStart}
              disabled={loading}
            >
              ▶ Start
            </button>
          ) : (
            <button
              style={{ ...s.btn, border: '1px solid #f59e0b', color: '#f59e0b' }}
              onClick={handlePause}
            >
              ⏸ Pause
            </button>
          )}
        </>
      )}
    </div>
  )
}
