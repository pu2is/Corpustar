import { defineStore } from 'pinia'

import { del, get, post } from '@/stores/fetchWrapper'
import { on } from '@/socket/socket'
import type { AddDocumentRequest, DocItem } from '@/types/documents'
import type { ProcessResponseWithId } from '@/types/general'

export const useDocumentStore = defineStore('document-store', {
  state: () => ({
    documents: [] as DocItem[],
    connected: false as boolean,
  }),
  getters: {
    getDocumentById: (state) => (docId: string): DocItem | null => {
      return state.documents.find((item) => item.id === docId) ?? null
    }
  },
  actions: {
    // 1. Socket binding
    bindSocketEvents(): void {
      if (this.connected) {
        return
      }

      on('socket:connected', () => {
        this.connected = true
        void this.getAllDocuments();
      })
      on('socket:disconnected', () => {
        this.connected = false
        this.documents = []
      })
      on('document:created', (socketMsg) => {
        const item = socketMsg as DocItem
        const existingIndex = this.documents.findIndex((doc) => doc.id === item.id)
        if (existingIndex >= 0) {
          this.documents.splice(existingIndex, 1, item)
          return
        }

        this.documents.unshift(item)
      })
      on('document:removed', (socketMsg) => {
        const removedId = (socketMsg as { id?: string })?.id
        if (!removedId) {
          return
        }

        const removeIndex = this.documents.findIndex((doc) => doc.id === removedId)
        if (removeIndex >= 0) {
          this.documents.splice(removeIndex, 1)
        }
      })
    },

    // 2. API requests
    async getAllDocuments(): Promise<DocItem[]> {
      const documents = await get<DocItem[]>('/api/documents')
      this.documents = documents
      return documents
    },

    async addDocumentByPath(filePath: string): Promise<ProcessResponseWithId> {
      const payload: AddDocumentRequest = { filePath }
      return post<ProcessResponseWithId>('/api/documents', payload)
    },

    async removeDocument(id: string): Promise<ProcessResponseWithId> {
      return del<ProcessResponseWithId>(`/api/documents/${encodeURIComponent(id)}`)
    },

  },
})
