import { SOCKET_EVENT } from './events'

const GLOBAL_SOCKET_KEY = '__corpustar_global_socket__'
const RECONNECT_DELAY_MS = 2000
const HEARTBEAT_INTERVAL_MS = 30000
export const SOCKET_CONNECTED_EVENT = SOCKET_EVENT.SOCKET_CONNECTED
export const SOCKET_DISCONNECTED_EVENT = SOCKET_EVENT.SOCKET_DISCONNECTED

type SocketEventHandler = (payload: unknown) => void
type SocketEnvelope = {
  event: string
  payload?: unknown
}

let heartbeatTimer: number | null = null
let reconnectTimer: number | null = null
let shouldReconnect = true
const eventHandlers = new Map<string, Set<SocketEventHandler>>()
const LEGACY_EVENT_ALIASES: Readonly<Record<string, readonly string[]>> = {
  [SOCKET_EVENT.SEGMENTATION_STARTED]: ['process:created'],
  [SOCKET_EVENT.SEGMENTATION_SUCCEED]: ['process:updated'],
  [SOCKET_EVENT.SEGMENTATION_FAILED]: ['process:updated'],
  [SOCKET_EVENT.IMPORT_RULE_SUCCEED]: ['rule:created'],
  [SOCKET_EVENT.RULE_ITEM_REMOVED]: ['rule:removed'],
  [SOCKET_EVENT.IMPORT_FVG_ENTRIES_SUCCEED]: ['fvgRules:created'],
  [SOCKET_EVENT.FVG_APPENDED]: ['fvgRule:appended'],
  [SOCKET_EVENT.FVG_REMOVED]: ['fvgRule:removed'],
  [SOCKET_EVENT.FVG_UPDATED]: ['fvgRule:updated'],
  [SOCKET_EVENT.LEMMATIZE_SUCCEED]: ['lemma:created'],
  [SOCKET_EVENT.SENTENCE_CORRECTED]: ['lemma:updated'],
}

function getGlobalScope(): typeof globalThis & { [GLOBAL_SOCKET_KEY]?: WebSocket } {
  return globalThis as typeof globalThis & { [GLOBAL_SOCKET_KEY]?: WebSocket }
}

function buildSocketUrl(): string {
  const explicit = import.meta.env.VITE_API_BASE_URL?.trim()
  const backendHost = import.meta.env.VITE_BACKEND_HOST?.trim()
  const backendPort = import.meta.env.VITE_BACKEND_PORT?.trim()

  if (!explicit && (!backendHost || !backendPort)) {
    throw new Error('Missing VITE_API_BASE_URL or VITE_BACKEND_HOST/VITE_BACKEND_PORT in frontend/.env')
  }

  const base = explicit || `http://${backendHost}:${backendPort}`
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

function clearReconnectTimer(): void {
  if (reconnectTimer !== null) {
    window.clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
}

function emitEvent(eventName: string, payload: unknown): void {
  const handlers = eventHandlers.get(eventName)
  if (!handlers || handlers.size === 0) {
    return
  }

  for (const handler of handlers) {
    try {
      handler(payload)
    } catch {
      // Ignore consumer exceptions to keep socket loop healthy.
    }
  }
}

function emitSocketEnvelope(eventName: string, payload: unknown): void {
  emitEvent(eventName, payload)

  const legacyAliases = LEGACY_EVENT_ALIASES[eventName]
  if (!legacyAliases || legacyAliases.length === 0) {
    return
  }

  for (const legacyEventName of legacyAliases) {
    if (legacyEventName === eventName) {
      continue
    }
    emitEvent(legacyEventName, payload)
  }
}

function isSocketEnvelope(message: unknown): message is SocketEnvelope {
  if (!message || typeof message !== 'object') {
    return false
  }

  const eventName = (message as { event?: unknown }).event
  return typeof eventName === 'string'
}

function scheduleReconnect(): void {
  if (!shouldReconnect || reconnectTimer !== null) {
    return
  }

  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = null
    connect()
  }, RECONNECT_DELAY_MS)
}

export function connect(): WebSocket {
  shouldReconnect = true

  const globalScope = getGlobalScope()
  const existing = globalScope[GLOBAL_SOCKET_KEY]
  if (existing && (existing.readyState === WebSocket.OPEN || existing.readyState === WebSocket.CONNECTING)) {
    return existing
  }

  const socket = new WebSocket(buildSocketUrl())
  globalScope[GLOBAL_SOCKET_KEY] = socket

  socket.addEventListener('open', () => {
    startHeartbeat(socket)
    emitEvent(SOCKET_CONNECTED_EVENT, undefined)
  })

  socket.addEventListener('close', () => {
    stopHeartbeat()
    if (getGlobalScope()[GLOBAL_SOCKET_KEY] === socket) {
      delete getGlobalScope()[GLOBAL_SOCKET_KEY]
    }
    emitEvent(SOCKET_DISCONNECTED_EVENT, undefined)
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

    if (!isSocketEnvelope(parsed)) {
      return
    }

    emitSocketEnvelope(parsed.event, parsed.payload)
  })

  return socket
}

export function disconnect(): void {
  shouldReconnect = false
  stopHeartbeat()
  clearReconnectTimer()

  const globalScope = getGlobalScope()
  const socket = globalScope[GLOBAL_SOCKET_KEY]
  if (!socket) {
    return
  }

  if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
    socket.close()
  }

  if (globalScope[GLOBAL_SOCKET_KEY] === socket) {
    delete globalScope[GLOBAL_SOCKET_KEY]
  }
}

export function on(eventName: string, handler: SocketEventHandler): () => void {
  let handlers = eventHandlers.get(eventName)
  if (!handlers) {
    handlers = new Set<SocketEventHandler>()
    eventHandlers.set(eventName, handlers)
  }

  handlers.add(handler)
  return () => {
    off(eventName, handler)
  }
}

export function off(eventName: string, handler: SocketEventHandler): void {
  const handlers = eventHandlers.get(eventName)
  if (!handlers) {
    return
  }

  handlers.delete(handler)
  if (handlers.size === 0) {
    eventHandlers.delete(eventName)
  }
}
