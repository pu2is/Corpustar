type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

type QueryPrimitive = string | number | boolean | null | undefined
type QueryValue = QueryPrimitive | QueryPrimitive[]

export type QueryParams = Record<string, QueryValue>

type JsonRecord = Record<string, unknown>

export interface FetchWrapperOptions extends Omit<RequestInit, 'method' | 'body'> {
  body?: BodyInit | JsonRecord | null
  params?: QueryParams
}

export class FetchWrapperError extends Error {
  public readonly status: number
  public readonly data: unknown

  constructor(message: string, status: number, data: unknown) {
    super(message)
    this.name = 'FetchWrapperError'
    this.status = status
    this.data = data
  }
}

const API_BASE_URL = resolveApiBaseUrl()

function resolveApiBaseUrl(): string {
  const explicit = import.meta.env.VITE_API_BASE_URL?.trim()
  if (explicit) {
    return trimTrailingSlash(explicit)
  }

  const backendHost = import.meta.env.BACKEND_HOST?.trim()
  const backendPort = import.meta.env.BACKEND_PORT?.trim()
  if (!backendHost || !backendPort) {
    throw new Error(
      'Missing VITE_API_BASE_URL or BACKEND_HOST/BACKEND_PORT in frontend/.env',
    )
  }

  return `http://${backendHost}:${backendPort}`
}

function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/u, '')
}

function isAbsoluteUrl(value: string): boolean {
  return /^https?:\/\//iu.test(value)
}

function buildUrl(path: string, params?: QueryParams): string {
  const normalizedPath = path.trim()
  if (!normalizedPath) {
    throw new Error('Request path is required')
  }

  const baseTarget = isAbsoluteUrl(normalizedPath)
    ? normalizedPath
    : `${trimTrailingSlash(API_BASE_URL)}/${normalizedPath.replace(/^\/+/u, '')}`

  const url = new URL(baseTarget)

  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value == null) {
        continue
      }

      if (Array.isArray(value)) {
        for (const item of value) {
          if (item != null) {
            url.searchParams.append(key, String(item))
          }
        }
        continue
      }

      url.searchParams.append(key, String(value))
    }
  }

  return url.toString()
}

function isJsonRecord(value: unknown): value is JsonRecord {
  if (value === null || typeof value !== 'object') {
    return false
  }

  const prototype = Object.getPrototypeOf(value)
  return prototype === Object.prototype || prototype === null
}

function encodeBody(body: FetchWrapperOptions['body'], headers: Headers): BodyInit | null | undefined {
  if (body === undefined) {
    return undefined
  }

  if (body === null) {
    return null
  }

  if (isJsonRecord(body)) {
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json')
    }

    return JSON.stringify(body)
  }

  return body
}

async function parseResponseBody(response: Response): Promise<unknown> {
  if (response.status === 204) {
    return undefined
  }

  const contentType = response.headers.get('content-type') ?? ''
  if (contentType.includes('application/json')) {
    try {
      return await response.json()
    } catch {
      return undefined
    }
  }

  const text = await response.text()
  return text || undefined
}

function readErrorMessage(payload: unknown, fallback: string): string {
  if (typeof payload === 'string' && payload.trim()) {
    return payload
  }

  if (payload && typeof payload === 'object' && 'message' in payload) {
    const message = (payload as { message?: unknown }).message
    if (typeof message === 'string' && message.trim()) {
      return message
    }
  }

  if (payload && typeof payload === 'object' && 'detail' in payload) {
    const detail = (payload as { detail?: unknown }).detail
    if (typeof detail === 'string' && detail.trim()) {
      return detail
    }
  }

  return fallback
}

export async function request<TResponse>(
  method: HttpMethod,
  path: string,
  options: FetchWrapperOptions = {},
): Promise<TResponse> {
  const { body, params, headers: rawHeaders, ...rest } = options
  const headers = new Headers(rawHeaders ?? {})

  const response = await fetch(buildUrl(path, params), {
    ...rest,
    method,
    headers,
    body: encodeBody(body, headers),
  })

  const payload = await parseResponseBody(response)
  if (!response.ok) {
    const message = readErrorMessage(payload, `Request failed with status ${response.status}`)
    throw new FetchWrapperError(message, response.status, payload)
  }

  return payload as TResponse
}

export function get<TResponse>(
  path: string,
  options: Omit<FetchWrapperOptions, 'body'> = {},
): Promise<TResponse> {
  return request<TResponse>('GET', path, options)
}

export function post<TResponse>(
  path: string,
  body?: FetchWrapperOptions['body'],
  options: Omit<FetchWrapperOptions, 'body'> = {},
): Promise<TResponse> {
  return request<TResponse>('POST', path, { ...options, body })
}

export function put<TResponse>(
  path: string,
  body?: FetchWrapperOptions['body'],
  options: Omit<FetchWrapperOptions, 'body'> = {},
): Promise<TResponse> {
  return request<TResponse>('PUT', path, { ...options, body })
}

export const push = put

export function patch<TResponse>(
  path: string,
  body?: FetchWrapperOptions['body'],
  options: Omit<FetchWrapperOptions, 'body'> = {},
): Promise<TResponse> {
  return request<TResponse>('PATCH', path, { ...options, body })
}

export function del<TResponse>(
  path: string,
  options: Omit<FetchWrapperOptions, 'body'> = {},
): Promise<TResponse> {
  return request<TResponse>('DELETE', path, options)
}
