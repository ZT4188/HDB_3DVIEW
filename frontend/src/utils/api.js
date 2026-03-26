const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`)
  return res.json()
}

// ── Buildings ───────────────────────────────────────────────
export const api = {
  buildings: {
    list: () => request('/buildings'),
    get: (id) => request(`/buildings/${id}`),
  },

  // ── Sessions ───────────────────────────────────────────────
  sessions: {
    list: () => request('/sessions'),
    create: (name) =>
      request(`/sessions?name=${encodeURIComponent(name)}`, { method: 'POST' }),
    get: (id) => request(`/sessions/${id}`),
    delete: (id) => request(`/sessions/${id}`, { method: 'DELETE' }),
    assign: (id) => request(`/sessions/${id}/assign`, { method: 'POST' }),
    start: (id) => request(`/sessions/${id}/start`, { method: 'POST' }),
    pause: (id) => request(`/sessions/${id}/pause`, { method: 'POST' }),
    snapshot: (id, year) => request(`/sessions/${id}/snapshot/${year}`),
  },
}
