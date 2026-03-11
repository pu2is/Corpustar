/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly BACKEND_HOST: string
  readonly BACKEND_PORT: string
  readonly FRONTEND_DEV_HOST: string
  readonly FRONTEND_DEV_PORT: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
