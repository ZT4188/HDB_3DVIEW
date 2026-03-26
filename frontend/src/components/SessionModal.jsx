import React, { useState, useEffect } from 'react'
import { useSimStore } from '../store/simStore.js'
import { api } from '../utils/api.js'

const s = {
  overlay: {
    position: 'fixed', inset: 0,
    background: 'rgba(0,0,0,0.7)',
    backdropFilter: 'blur(4px)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    zIndex: 1000,
    fontFamily: "'DM Mono', monospace",
  },
  modal: {
    background: '#111318',
    border: '1px solid #242830',
    borderRadius: 16,
    width: 480,
    maxHeight: '80vh',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  header: {
    padding: '18px 22px',
    borderBottom: '1px solid #242830',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    fontFamily: "'Syne', sans-serif",
    fontSize: 16,
    fontWeight: 700,
    color: '#fff',
  },
  close: {
    background: 'none', border: 'none', color: '#6b7280',
    cursor: 'pointer', fontSize: 20, lineHeight: 1,
  },
  createRow: {
    padding: '16px 22px',
    borderBottom: '1px solid #242830',
    display: 'flex',
    gap: 8,
  },
  input: {
    flex: 1,
    background: '#181c24',
    border: '1px solid #242830',
    borderRadius: 8,
    color: '#e8ecf0',
    fontFamily: "'DM Mono', monospace",
    fontSize: 13,
    padding: '8px 12px',
    outline: 'none',
  },
  btnCreate: {
    background: '#00e5a0',
    border: 'none',
    borderRadius: 8,
    color: '#0a0c10',
    cursor: 'pointer',
    fontFamily: "'Syne', sans-serif",
    fontWeight: 700,
    fontSize: 13,
    padding: '8px 16px',
    whiteSpace: 'nowrap',
  },
  list: {
    flex: 1,
    overflowY: 'auto',
    padding: '8px 0',
  },
  item: {
    padding: '12px 22px',
    borderBottom: '1px solid #1c2028',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    cursor: 'pointer',
    transition: 'background 0.1s',
  },
  itemName: {
    fontFamily: "'Syne', sans-serif",
    fontSize: 14,
    fontWeight: 600,
    color: '#e8ecf0',
    marginBottom: 3,
  },
  itemMeta: { fontSize: 11, color: '#6b7280' },
  activeDot: {
    width: 8, height: 8, borderRadius: '50%', background: '#00e5a0',
    boxShadow: '0 0 8px #00e5a0', flexShrink: 0,
  },
  deleteBtn: {
    background: 'none', border: 'none', color: '#6b7280',
    cursor: 'pointer', fontSize: 16, padding: '0 4px',
    marginLeft: 8,
  },
  empty: { color: '#4b5563', fontSize: 12, textAlign: 'center', padding: '32px' },
}

export default function SessionModal() {
  const {
    showSessionModal, setShowSessionModal,
    sessions, setSessions,
    activeSession, setActiveSession,
    setSimStatus,
  } = useSimStore()
  const [newName, setNewName] = useState('')

  const load = () => api.sessions.list().then(setSessions).catch(console.error)

  useEffect(() => {
    if (showSessionModal) load()
  }, [showSessionModal])

  if (!showSessionModal) return null

  const handleCreate = async () => {
    if (!newName.trim()) return
    await api.sessions.create(newName.trim())
    setNewName('')
    load()
  }

  const handleSelect = (session) => {
    setActiveSession(session)
    setSimStatus(session.status || 'idle')
    setShowSessionModal(false)
  }

  const handleDelete = async (e, id) => {
    e.stopPropagation()
    await api.sessions.delete(id)
    load()
    if (activeSession?.id === id) setActiveSession(null)
  }

  return (
    <div style={s.overlay} onClick={() => setShowSessionModal(false)}>
      <div style={s.modal} onClick={(e) => e.stopPropagation()}>
        <div style={s.header}>
          <span style={s.title}>Simulation Sessions</span>
          <button style={s.close} onClick={() => setShowSessionModal(false)}>×</button>
        </div>

        <div style={s.createRow}>
          <input
            style={s.input}
            placeholder="Session name…"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
          />
          <button style={s.btnCreate} onClick={handleCreate}>Create</button>
        </div>

        <div style={s.list}>
          {sessions.length === 0 ? (
            <div style={s.empty}>No sessions yet — create one above.</div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                style={{
                  ...s.item,
                  background: activeSession?.id === session.id ? 'rgba(0,229,160,0.05)' : 'transparent',
                }}
                onClick={() => handleSelect(session)}
              >
                <div>
                  <div style={s.itemName}>{session.name}</div>
                  <div style={s.itemMeta}>
                    Year {session.current_year} · {session.years_simulated} yrs ·{' '}
                    {(session.total_residents || 0).toLocaleString()} residents
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  {activeSession?.id === session.id && <div style={s.activeDot} />}
                  <button
                    style={s.deleteBtn}
                    onClick={(e) => handleDelete(e, session.id)}
                    title="Delete session"
                  >×</button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
