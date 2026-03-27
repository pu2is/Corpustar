function normalizeSegment(value: string | undefined, fallback: string): string {
  const trimmed = value?.trim() ?? ''
  const raw = trimmed || fallback
  const normalized = raw.replace(/^\/+|\/+$/gu, '')
  return normalized || fallback
}

function normalizePath(value: string): string {
  return value.replace(/\/+$/u, '') || '/'
}

const documentSegment = normalizeSegment(import.meta.env.VITE_ENDPOINT_DOCUMENTS, 'documents')
const ruleSegment = normalizeSegment(import.meta.env.VITE_ENDPOINT_RULES, 'rules')

export const APP_ROUTES = {
  root: '/',
  documents: `/${documentSegment}`,
  documentDetail: (id: string) => `/${documentSegment}/${encodeURIComponent(id)}`,
  rules: `/${ruleSegment}`,
  ruleDetail: (id: string) => `/${ruleSegment}/${encodeURIComponent(id)}`,
} as const

export function isInRouteSection(path: string, sectionBasePath: string): boolean {
  const normalizedPath = normalizePath(path)
  const normalizedSection = normalizePath(sectionBasePath)

  return normalizedPath === normalizedSection || normalizedPath.startsWith(`${normalizedSection}/`)
}
