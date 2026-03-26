import React from 'react'
import { useSimStore } from '../store/simStore.js'

const styles = {
  panel: {
    position: 'absolute',
    top: 20,
    left: 20,
    width: 300,
    background: 'rgba(17,19,24,0.95)',
    border: '1px solid #242830',
    borderRadius: 12,
    backdropFilter: 'blur(12px)',
    overflow: 'hidden',
    fontFamily: "'DM Mono', monospace",
    transition: 'opacity 0.2s, transform 0.2s',
  },
  header: {
    padding: '14px 18px',
    borderBottom: '1px solid #242830',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  label: { fontSize: 10, color: '#6b7280', letterSpacing: '0.15em', textTransform: 'uppercase' },
  close: {
    background: 'none', border: 'none', color: '#6b7280',
    cursor: 'pointer', fontSize: 18, lineHeight: 1, padding: '0 2px',
  },
  body: { padding: '16px 18px' },
  address: { fontFamily: "'Syne', sans-serif", fontSize: 15, fontWeight: 700, color: '#fff', marginBottom: 14, lineHeight: 1.4 },
  row: { display: 'flex', justifyContent: 'space-between', padding: '7px 0', borderBottom: '1px solid #242830', fontSize: 12 },
  rowKey: { color: '#6b7280' },
  rowVal: { color: '#e8ecf0', fontWeight: 500 },
  resRow: {
    display: 'flex', justifyContent: 'space-between', padding: '7px 0',
    borderBottom: '1px solid #242830', fontSize: 12,
  },
  resLabel: { fontSize: 10, color: '#6b7280', letterSpacing: '0.1em', textTransform: 'uppercase', marginTop: 14, marginBottom: 4 },
  occupancyBar: {
    height: 4, borderRadius: 2, background: '#242830', marginTop: 10, overflow: 'hidden',
  },
}

export default function InfoPanel() {
  const { selectedBuilding, setSelectedBuilding, residentMap } = useSimStore()

  if (!selectedBuilding) return null

  const residents = residentMap[selectedBuilding.id]
  const capacity = (selectedBuilding.dwelling_units || 1) * 3
  const occupancy = residents != null ? Math.min(1, residents / capacity) : null

  const unitRows = [
    ['1-Room', selectedBuilding.units?.['1_room']],
    ['2-Room', selectedBuilding.units?.['2_room']],
    ['3-Room', selectedBuilding.units?.['3_room']],
    ['4-Room', selectedBuilding.units?.['4_room']],
    ['5-Room', selectedBuilding.units?.['5_room']],
  ]

  return (
    <div style={styles.panel}>
      <div style={styles.header}>
        <span style={styles.label}>Selected Building</span>
        <button style={styles.close} onClick={() => setSelectedBuilding(null)}>×</button>
      </div>
      <div style={styles.body}>
        <div style={styles.address}>{selectedBuilding.address}</div>

        <div style={styles.row}>
          <span style={styles.rowKey}>Block No.</span>
          <span style={styles.rowVal}>{selectedBuilding.blk_no}</span>
        </div>
        <div style={styles.row}>
          <span style={styles.rowKey}>Total Dwelling Units</span>
          <span style={styles.rowVal}>{(selectedBuilding.dwelling_units || 0).toLocaleString()}</span>
        </div>

        {residents != null && (
          <div style={styles.row}>
            <span style={styles.rowKey}>Current Residents</span>
            <span style={{ ...styles.rowVal, color: '#00e5a0' }}>{residents.toLocaleString()}</span>
          </div>
        )}

        <div style={styles.resLabel}>Unit Breakdown</div>
        {unitRows.map(([label, count]) => (
          <div key={label} style={styles.resRow}>
            <span style={styles.rowKey}>{label}</span>
            <span style={styles.rowVal}>{(count || 0).toLocaleString()}</span>
          </div>
        ))}

        {occupancy != null && (
          <>
            <div style={{ ...styles.resLabel, marginTop: 14 }}>
              Occupancy — {Math.round(occupancy * 100)}%
            </div>
            <div style={styles.occupancyBar}>
              <div style={{
                height: '100%',
                width: `${occupancy * 100}%`,
                background: occupancy < 0.5 ? '#22c55e' : occupancy < 0.8 ? '#f59e0b' : '#ef4444',
                transition: 'width 0.6s ease',
              }} />
            </div>
          </>
        )}
      </div>
    </div>
  )
}
