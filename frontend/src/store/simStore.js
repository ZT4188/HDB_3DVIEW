import { create } from 'zustand'

export const useSimStore = create((set, get) => ({
  // ── Sessions ──────────────────────────────────────────────
  sessions: [],
  activeSession: null,
  showSessionModal: false,

  setSessions: (sessions) => set({ sessions }),
  setActiveSession: (session) => set({ activeSession: session }),
  setShowSessionModal: (show) => set({ showSessionModal: show }),

  // ── Buildings ─────────────────────────────────────────────
  buildings: [],          // GeoJSON FeatureCollection features
  selectedBuilding: null, // Full building detail from API
  residentMap: {},        // { building_id: resident_count }

  setBuildings: (buildings) => set({ buildings }),
  setSelectedBuilding: (b) => set({ selectedBuilding: b }),
  setResidentMap: (map) => set({ residentMap: map }),

  // ── Simulation state ──────────────────────────────────────
  simStatus: 'idle',      // idle | running | paused
  currentYear: 2025,
  yearsSimulated: 0,
  totalResidents: 0,
  totalDeaths: 0,
  totalBirths: 0,
  moveLog: [],            // [ { from_id, to_id, count, year } ]

  setSimStatus: (status) => set({ simStatus: status }),

  applyTick: (tick) => set((state) => ({
    currentYear: tick.year,
    yearsSimulated: tick.years_simulated,
    totalResidents: tick.total_residents,
    totalDeaths: (state.totalDeaths || 0) + (tick.total_deaths || 0),
    totalBirths: (state.totalBirths || 0) + (tick.total_births || 0),
    residentMap: { ...state.residentMap, ...tick.resident_deltas },
    moveLog: [
      ...tick.move_log.map((m) => ({ ...m, year: tick.year })),
      ...state.moveLog,
    ].slice(0, 200),
  })),

  // ── Timeline ──────────────────────────────────────────────
  timelineYear: null,     // null = live mode; number = replay mode
  maxYear: 2025,

  setTimelineYear: (year) => set({ timelineYear: year }),
  setMaxYear: (year) => set({ maxYear: year }),

  // Apply a historical snapshot for timeline replay
  applySnapshot: (snapshot) => set({
    currentYear: snapshot.year,
    totalResidents: snapshot.total_residents,
    totalDeaths: snapshot.total_deaths,
    residentMap: snapshot.resident_map,
    moveLog: snapshot.move_log.map((m) => ({ ...m, year: snapshot.year })),
  }),
}))
