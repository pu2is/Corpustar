import { defineStore } from 'pinia';

import { post } from '@/store/fetchWrapper';
import type { DocItem } from '@/types/documents';

interface DocumentState {
  documents: DocItem[]
  loading: boolean
  error: string | null
}

export const useDocumentStore = defineStore('document-store', {
  state: (): DocumentState => ({
    documents: [],
    loading: false,
    error: null,
  }),
  actions: {
    // Post
    async addDocumentByPath(filePath: string): Promise<DocItem> {
      this.loading = true;
      this.error = null;

      try {
        const doc = await post<DocItem>('/api/add_document', { filePath });
        this.documents.unshift(doc);
        return doc;
      } catch (error) {
        this.error = error instanceof Error ? error.message : String(error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
  },
})
