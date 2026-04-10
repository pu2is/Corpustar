/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly VITE_SENTENCE_ITEM_PER_PAGE?: string
  readonly VITE_BACKEND_HOST?: string
  readonly VITE_BACKEND_PORT?: string
  readonly VITE_FRONTEND_DEV_HOST?: string
  readonly VITE_FRONTEND_DEV_PORT?: string
  readonly VITE_ENDPOINT_DOCUMENTS?: string
  readonly VITE_ENDPOINT_RULES?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

interface Window {
  electronAPI?: {
    selectDocumentFile(): Promise<string | null>
    selectRuleFile(): Promise<string | null>
    readDocumentText(filePath: string): Promise<string>
      selectSavePath(defaultFilename: string): Promise<{ dir: string; filename: string } | null>
