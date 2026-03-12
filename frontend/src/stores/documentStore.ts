import { defineStore } from 'pinia';
// fetch wrapper
import { del, get, post } from '@/stores/fetchWrapper';
// types
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
    removeDocumentFromStore(id: string): void {
      this.documents = this.documents.filter((doc) => doc.id !== id);
    },

    handleDocumentRemoved(payload: { id?: string } | null | undefined): void {
      const removedId = payload?.id;
      if (!removedId) {
        return;
      }

      this.removeDocumentFromStore(removedId);
    },

    async getAllDocuments(): Promise<DocItem[]> {
      this.loading = true;
      this.error = null;

      try {
        const documents = await get<DocItem[]>('/api/documents');
        this.documents = documents;
        return documents;
      } catch (error) {
        this.error = error instanceof Error ? error.message : String(error);
        throw error;
      } finally {
        this.loading = false;
      }
    },

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

    // Delete
    async removeDocument(id: string): Promise<void> {
      this.loading = true;
      this.error = null;

      try {
        const response = await del<{ success: boolean; id: string }>(`/api/remove_document/${encodeURIComponent(id)}`);
        this.removeDocumentFromStore(response.id);
      } catch (error) {
        this.error = error instanceof Error ? error.message : String(error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
  },
})
