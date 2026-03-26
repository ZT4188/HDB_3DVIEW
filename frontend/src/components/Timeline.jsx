import React, { useRef, useEffect, useState } from 'react'
import { useSimStore } from '../store/simStore.js'
import { api } from '../utils/api.js'

const s = {
  bar: {
    position: 'absolute',
    bottom: 18,
    left: '50%',
    transform: 'translateX(-50%)',
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    background: 'rgba(17,19,24,0.95)',
    border: '1px solid #242830',
    borderRadius: 8,
    padding: '8px 16px',
    backdropFilter: 'blur(12px)',
    fontFamily: "'DM Mono', monospace",
    fontSize: 11,
    width: 'min(600px, calc(100vw - 680px))',
    minWidth: 280,
  },
  yearLabel: {
    color: '#6b7280',
    whiteSpace: 'nowrap',
    minWidth: 38,
  },
  slider: {
    flex: 1,
    accentColor: '#00e5a0',
    cursor: 'pointer',
    height: 4,
  },
  liveBtn: {
    background: 'none',
    border: '1px solid #242830',
    borderRadius: 4,
    color: '#6b7280',
    cursor: 'pointer',
    fontSize: 10,
    padding: '3px 8px',
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    whiteSpace: 'nowrap',
  },
  liveBtnActive: {
    borderColor: '#00e5a0',
    color: '#00e5a0',
  },
}

export default function Timeline() {
  const { activeSession, currentYear, maxYear, timelineYear, setTimelineYear, applySnapshot } = useSimStore()
  const [playback, setPlayback] = useState(false)
  const playRef = useRef(null)

  const startYear = 2025
  const endYear = maxYear

  const handleScrub = async (e) => {
    const year = parseInt(e.target.value)
    if (year === maxYear) {
      setTimelineYear(null)
      return
    }
    setTimelineYear(year)
    if (!activeSession) return
    try {
      const snap = await api.sessions.snapshot(activeSession.id, year)
      applySnapshot(snap)
    } catch (err) {
      console.warn('No snapshot for year', year)
    }
  }

  const handlePlayback = () => {
    if (playback) {
      clearInterval(playRef.current)
      setPlayback(false)
      return
    }
    setPlayback(true)
    let year = timelineYear ?? startYear
    playRef.current = setInterval(async () => {
      year++
      if (year > endYear) {
        clearInterval(playRef.current)
        setPlayback(false)
        setTimelineYear(null)
        return
      }
      setTimelineYear(year)
      if (!activeSession) return
      try {
        const snap = await api.sessions.snapshot(activeSession.id, year)
        applySnapshot(snap)
      } catch {}
    }, 300)
  }

  useEffect(() => () => clearInterval(playRef.current), [])

  if (endYear <= startYear) return null

  return (
    <div style={s.bar}>
      <button
        style={s.liveBtn}
        onClick={handlePlayback}
        title={playback ? 'Stop playback' : 'Play from start'}
      >
        {playback ? '⏹' : '▶'}
      </button>

      <span style={s.yearLabel}>{timelineYear ?? currentYear}</span>

      <input
        type="range"
        style={s.slider}
        min={startYear}
        max={endYear}
        value={timelineYear ?? endYear}
        onChange={handleScrub}
      />

      <span style={s.yearLabel}>{endYear}</span>

      <button
        style={{ ...s.liveBtn, ...(timelineYear == null ? s.liveBtnActive : {}) }}
        onClick={() => setTimelineYear(null)}
        title="Jump to live"
      >
        LIVE
      </button>
    </div>
  )
}
