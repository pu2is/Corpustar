export type DocFileType = 'doc' | 'docx' | 'odt' | 'txt'

export interface DocItem {
  id: string
  filename: string
  display_name: string
  note: string
  source_path: string
  text_path: string
  char_count: number
  file_type: DocFileType
  file_size: number
  created_at: string
  updated_at: string
}

export interface AddDocumentRequest extends Record<string, unknown> {
  filePath: string
}
