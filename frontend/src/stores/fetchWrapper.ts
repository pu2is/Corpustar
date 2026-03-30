import axios from 'axios'
import type { AxiosRequestConfig } from 'axios'

type QueryPrimitive = string | number | boolean | null | undefined
type QueryValue = QueryPrimitive | QueryPrimitive[]

export type QueryParams = Record<string, QueryValue>

export interface FetchWrapperOptions
  extends Omit<AxiosRequestConfig, 'baseURL' | 'url' | 'method' | 'data' | 'params'> {
  body?: unknown
  params?: QueryParams
}

const client = axios.create({
  baseURL: resolveApiBaseUrl(),
})

function resolveApiBaseUrl(): string {
  const explicit = import.meta.env.VITE_API_BASE_URL?.trim()
  if (explicit) {
    return explicit.replace(/\/+$/u, '')
  }

  const backendHost = import.meta.env.VITE_BACKEND_HOST?.trim()
  const backendPort = import.meta.env.VITE_BACKEND_PORT?.trim()
  if (!backendHost || !backendPort) {
    throw new Error('Missing VITE_API_BASE_URL or VITE_BACKEND_HOST/VITE_BACKEND_PORT in frontend/.env')
  }

  return `http://${backendHost}:${backendPort}`
}

function normalizePath(path: string): string {
  const value = path.trim()
  if (!value) {
    throw new Error('Request path is required')
  }

  if (/^https?:\/\//iu.test(value)) {
    return value
  }

  return value.startsWith('/') ? value : `/${value}`
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

async function send<TResponse>(
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE',
  path: string,
  options: FetchWrapperOptions = {},
): Promise<TResponse> {
  const { body, ...rest } = options

  try {
    const response = await client.request<TResponse>({
      ...rest,
      method,
      url: normalizePath(path),
      data: body,
    })

    return response.data
  } catch (error) {
    if (!axios.isAxiosError(error) || error.code === 'ERR_CANCELED') {
      throw error
    }

    throw new Error(readErrorMessage(error.response?.data, error.message))
  }
}

export function get<TResponse>(path: string, options: Omit<FetchWrapperOptions, 'body'> = {}): Promise<TResponse> {
  return send<TResponse>('GET', path, options)
}

export function post<TResponse>(
  path: string,
  body?: FetchWrapperOptions['body'],
  options: Omit<FetchWrapperOptions, 'body'> = {},
): Promise<TResponse> {
  return send<TResponse>('POST', path, { ...options, body })
}

export function del<TResponse>(
  path: string,
  options: Omit<FetchWrapperOptions, 'body'> = {},
): Promise<TResponse> {
  return send<TResponse>('DELETE', path, options)
}

export function put<TResponse>(
  path: string,
  body?: FetchWrapperOptions['body'],
  options: Omit<FetchWrapperOptions, 'body'> = {},
): Promise<TResponse> {
  return send<TResponse>('PUT', path, { ...options, body })
}

export function patch<TResponse>(
  path: string,
  body?: FetchWrapperOptions['body'],
  options: Omit<FetchWrapperOptions, 'body'> = {},
): Promise<TResponse> {
  return send<TResponse>('PATCH', path, { ...options, body })
}
