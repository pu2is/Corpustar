const GLOBAL_SOCKET_KEY = '__corpustar_global_socket__'
const RECONNECT_DELAY_MS = 2000
const HEARTBEAT_INTERVAL_MS = 30000

let heartbeatTimer: number | null = null
let reconnectTimer: number | null = null
let documentStore: {
  getAllDocuments: () => Promise<unknown>
  handleDocumentRemoved?: (payload: { id?: string } | null | undefined) => void
} | null = null

function buildSocketUrl(): string {
  const explicit = import.meta.env.VITE_API_BASE_URL?.trim()
  const base =
    explicit || `http://${import.meta.env.BACKEND_HOST.trim()}:${import.meta.env.BACKEND_PORT.trim()}`
  const url = new URL(base)

  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  url.pathname = '/ws'
  url.search = ''
  url.hash = ''

  return url.toString()
}

function startHeartbeat(socket: WebSocket): void {
  stopHeartbeat()
  heartbeatTimer = window.setInterval(() => {
    if (socket.readyState === WebSocket.OPEN) {
      socket.send('ping')
    }
  }, HEARTBEAT_INTERVAL_MS)
}

function stopHeartbeat(): void {
  if (heartbeatTimer !== null) {
    window.clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
}

function scheduleReconnect(): void {
  if (reconnectTimer !== null) {
    return
  }

  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = null
    connectGlobalSocket()
  }, RECONNECT_DELAY_MS)
}

export function connectGlobalSocket(store?: {
  getAllDocuments: () => Promise<unknown>
  handleDocumentRemoved?: (payload: { id?: string } | null | undefined) => void
}): WebSocket {
  if (store) {
    documentStore = store
  }

  const globalScope = globalThis as typeof globalThis & {
    [GLOBAL_SOCKET_KEY]?: WebSocket
  }

  const existing = globalScope[GLOBAL_SOCKET_KEY]
  if (existing && (existing.readyState === WebSocket.OPEN || existing.readyState === WebSocket.CONNECTING)) {
    return existing
  }

  const socket = new WebSocket(buildSocketUrl())
  globalScope[GLOBAL_SOCKET_KEY] = socket

  socket.addEventListener('open', () => {
    startHeartbeat(socket)
    if (documentStore) {
      void documentStore.getAllDocuments().catch(() => undefined)
    }
  })

  socket.addEventListener('close', () => {
    stopHeartbeat()
    scheduleReconnect()
  })

  socket.addEventListener('error', () => {
    stopHeartbeat()
    scheduleReconnect()
  })

  socket.addEventListener('message', (event) => {
    if (typeof event.data !== 'string') {
      return
    }

    if (event.data === 'pong') {
      return
    }

    let parsed: unknown
    try {
      parsed = JSON.parse(event.data)
    } catch {
      return
    }

    if (!parsed || typeof parsed !== 'object') {
      return
    }

    const eventName = (parsed as { event?: unknown }).event
    const payload = (parsed as { payload?: unknown }).payload

    if (eventName === 'document:removed' && documentStore?.handleDocumentRemoved) {
      documentStore.handleDocumentRemoved(
        payload && typeof payload === 'object' ? (payload as { id?: string }) : undefined,
      )
    }
  })

  return socket
}
