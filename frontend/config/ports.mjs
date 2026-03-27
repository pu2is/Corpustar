import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const frontendRoot = path.resolve(__dirname, '..')

function parseEnvFile(filePath) {
  if (!existsSync(filePath)) {
    return {}
  }

  const fileContent = readFileSync(filePath, 'utf8')
  const env = {}

  for (const rawLine of fileContent.split(/\r?\n/u)) {
    const line = rawLine.trim()
    if (!line || line.startsWith('#')) {
      continue
    }

    const separatorIndex = line.indexOf('=')
    if (separatorIndex <= 0) {
      continue
    }

    const key = line.slice(0, separatorIndex).trim()
    let value = line.slice(separatorIndex + 1).trim()

    if (value.length >= 2) {
      const quote = value[0]
      if ((quote === '"' || quote === "'") && value[value.length - 1] === quote) {
        value = value.slice(1, -1)
      }
    }

    env[key] = value
  }

  return env
}

function loadEnv() {
  const envFromFile = {
    ...parseEnvFile(path.join(frontendRoot, '.env')),
    ...parseEnvFile(path.join(frontendRoot, '.env.local')),
  }

  return {
    ...envFromFile,
    ...process.env,
  }
}

function readRequired(env, key) {
  const value = env[key]
  if (typeof value !== 'string' || value.trim() === '') {
    throw new Error(`[ports] Missing required env key "${key}" in frontend/.env`)
  }

  return value.trim()
}

function readRequiredPort(env, key) {
  const raw = readRequired(env, key)
  const port = Number(raw)
  if (!Number.isInteger(port) || port <= 0 || port > 65535) {
    throw new Error(`[ports] Invalid port "${raw}" for env key "${key}"`)
  }

  return port
}

const env = loadEnv()

export const FRONTEND_DEV_HOST = readRequired(env, 'VITE_FRONTEND_DEV_HOST')
export const FRONTEND_DEV_PORT = readRequiredPort(env, 'VITE_FRONTEND_DEV_PORT')
export const BACKEND_HOST = readRequired(env, 'VITE_BACKEND_HOST')
export const BACKEND_PORT = readRequiredPort(env, 'VITE_BACKEND_PORT')

export const FRONTEND_DEV_URL = `http://${FRONTEND_DEV_HOST}:${FRONTEND_DEV_PORT}`
export const BACKEND_BASE_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`

