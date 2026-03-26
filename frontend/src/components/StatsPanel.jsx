import React from 'react'
import { useSimStore } from '../store/simStore.js'

const s = {
  panel: {
    position: 'absolute',
    top: 20,
    right: 20,
    width: 280,
    maxHeight: 'calc(100vh - 120px)',
    background: 'rgba(17,19,24,0.95)',
    border: '1px solid #242830',
    borderRadius: 12,
    backdropFilter: 'blur(12px)',
    fontFamily: "'DM Mono', monospace",
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  header: {
    padding: '14px 18px',
    borderBottom: '1px solid #242830',
    fontSize: 10,
    color: '#6b7280',
    letterSpacing: '0.15em',
    textTransform: 'uppercase',
    flexShrink: 0,
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 1,
    background: '#242830',
    borderBottom: '1px solid #242830',
    flexShrink: 0,
  },
  statCell: {
    background: 'rgba(17,19,24,0.95)',
    padding: '14px 16px',
  },
  statVal: {
    fontFamily: "'Syne', sans-serif",
    fontSize: 22,
    fontWeight: 800,
    color: '#00e5a0',
    lineHeight: 1,
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 9,
    color: '#6b7280',
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
  },
  logHeader: {
    padding: '12px 18px 8px',
    fontSize: 10,
    color: '#6b7280',
    letterSpacing: '0.15em',
    textTransform: 'uppercase',
    flexShrink: 0,
  },
  logList: {
    flex: 1,
    overflowY: 'auto',
    padding: '0 18px 14px',
  },
  logEntry: {
    fontSize: 11,
    color: '#9ca3af',
    padding: '5px 0',
    borderBottom: '1px solid #1c2028',
    lineHeight: 1.5,
  },
  logYear: { color: '#3b82f6', marginRight: 6 },
  logCount: { color: '#e8ecf0' },
  empty: {
    color: '#4b5563',
    fontSize: 11,
    textAlign: 'center',
    padding: '20px 0',
  },
}

function fmt(n) {
  return (n || 0).toLocaleString()
}

function shortId(id) {
  return id ? id.slice(0, 8) + '…' : '?'
}

export default function StatsPanel() {
  const {
    activeSession,
    currentYear, yearsSimulated,
    totalResidents, totalDeaths, totalBirths,
    moveLog, simStatus,
  } = useSimStore()

  return (
    <div style={s.panel}>
      <div style={s.header}>Simulation Stats</div>

      <div style={s.statsGrid}>
        <div style={s.statCell}>
          <div style={s.statVal}>{currentYear}</div>
          <div style={s.statLabel}>Current Year</div>
        </div>
        <div style={s.statCell}>
          <div style={s.statVal}>{yearsSimulated}</div>
          <div style={s.statLabel}>Years Run</div>
        </div>
        <div style={s.statCell}>
          <div style={{ ...s.statVal, fontSize: 16 }}>{fmt(totalResidents)}</div>
          <div style={s.statLabel}>Total Residents</div>
        </div>
        <div style={s.statCell}>
          <div style={{ ...s.statVal, color: '#f87171', fontSize: 16 }}>{fmt(totalDeaths)}</div>
          <div style={s.statLabel}>Total Deaths</div>
        </div>
        <div style={{ ...s.statCell, gridColumn: '1 / -1' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              width: 8, height: 8, borderRadius: '50%',
              background: simStatus === 'running' ? '#00e5a0'
                : simStatus === 'paused' ? '#f59e0b' : '#6b7280',
              boxShadow: simStatus === 'running' ? '0 0 8px #00e5a0' : 'none',
            }} />
            <span style={{ ...s.statLabel, color: '#e8ecf0' }}>
              {activeSession ? activeSession.name : 'No session'}
              {simStatus !== 'idle' && ` · ${simStatus}`}
            </span>
          </div>
        </div>
      </div>

      <div style={s.logHeader}>Move Log</div>
      <div style={s.logList}>
        {moveLog.length === 0 ? (
          <div style={s.empty}>No moves yet — start the simulation.</div>
        ) : (
          moveLog.map((entry, i) => (
            <div key={i} style={s.logEntry}>
              <span style={s.logYear}>{entry.year}</span>
              <span style={s.logCount}>{entry.count}</span>
              {' '}resident{entry.count !== 1 ? 's' : ''} moved{' '}
              {shortId(entry.from_id)} → {shortId(entry.to_id)}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
