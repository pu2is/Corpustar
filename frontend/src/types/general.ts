export interface ProcessResponseWithId {
  id: string
  ok: boolean
  err_msg?: string
  error_msg?: string
}

export interface ProcessResponse {
  ok: boolean
  err_msg?: string
  error_msg?: string
}
