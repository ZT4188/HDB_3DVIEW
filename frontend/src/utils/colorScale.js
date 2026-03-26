/**
 * Maps occupancy ratio (0–1) to an RGBA colour array.
 * 0.0 (empty)  → cool green  [34, 197, 94]
 * 0.5 (half)   → amber       [245, 158, 11]
 * 1.0 (full)   → deep red    [239, 68, 68]
 */

const STOPS = [
  { t: 0.0,  r: 34,  g: 197, b: 94  },  // green
  { t: 0.4,  r: 163, g: 230, b: 53  },  // lime
  { t: 0.65, r: 245, g: 158, b: 11  },  // amber
  { t: 0.85, r: 249, g: 115, b: 22  },  // orange
  { t: 1.0,  r: 239, g: 68,  b: 68  },  // red
]

function lerp(a, b, t) {
  return Math.round(a + (b - a) * t)
}

export function occupancyColor(ratio, alpha = 220) {
  const clamped = Math.max(0, Math.min(1, ratio))

  let lo = STOPS[0]
  let hi = STOPS[STOPS.length - 1]

  for (let i = 0; i < STOPS.length - 1; i++) {
    if (clamped >= STOPS[i].t && clamped <= STOPS[i + 1].t) {
      lo = STOPS[i]
      hi = STOPS[i + 1]
      break
    }
  }

  const span = hi.t - lo.t
  const t = span === 0 ? 0 : (clamped - lo.t) / span

  return [
    lerp(lo.r, hi.r, t),
    lerp(lo.g, hi.g, t),
    lerp(lo.b, hi.b, t),
    alpha,
  ]
}

/** Default colour for buildings with no data */
export const DEFAULT_COLOR = [60, 70, 90, 180]
