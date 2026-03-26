import { useEffect, useRef } from 'react'
import { useSimStore } from '../store/simStore.js'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export function useWebSocket(sessionId) {
  const wsRef = useRef(null)
  const { applyTick, setMaxYear } = useSimStore()

  useEffect(() => {
    if (!sessionId) return

    const connect = () => {
      const ws = new WebSocket(`${WS_URL}/ws/sessions/${sessionId}`)
      wsRef.current = ws

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.type === 'tick') {
          applyTick(data)
          setMaxYear(data.year)
        }
      }

      ws.onclose = () => {
        // Auto-reconnect after 2s
        setTimeout(connect, 2000)
      }

      ws.onerror = (err) => {
        console.warn('WebSocket error:', err)
        ws.close()
      }
    }

    connect()

    return () => {
      wsRef.current?.close()
    }
  }, [sessionId])
}
