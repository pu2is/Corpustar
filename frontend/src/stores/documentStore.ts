import { defineStore } from 'pinia';
// fetch wrapper
import { del, get, post } from '@/stores/fetchWrapper';
import { on } from '@/socket/socket';
// types
import type { DocItem } from '@/types/documents';

interface DocumentState {
  documents: DocItem[]
  loading: boolean
  error: string | null
  socketBound: boolean
  socketUnsubscribers: Array<() => void>
}

const DOC_FILE_TYPES = new Set(['doc', 'docx', 'odt', 'txt']);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function toNonEmptyString(value: unknown): string | null {
  if (typeof value !== 'string') {
    return null;
  }

  const trimmed = value.trim();
  return trimmed.length ? trimmed : null;
}

function toDocItemFromCreatedPayload(value: unknown): DocItem | null {
  if (!isRecord(value)) {
    return null;
  }

  const id = toNonEmptyString(value.id);
  const filename = toNonEmptyString(value.filename);
  const displayName = toNonEmptyString(value.displayName);
  const fileType = toNonEmptyString(value.fileType);
  const createdAt = toNonEmptyString(value.createdAt);
  const updatedAt = toNonEmptyString(value.updatedAt);
  const fileSize = typeof value.fileSize === 'number' ? value.fileSize : null;

  if (!id || !filename || !displayName || !fileType || !createdAt || !updatedAt || fileSize === null) {
    return null;
  }

  if (!Number.isFinite(fileSize) || !DOC_FILE_TYPES.has(fileType)) {
    return null;
  }

  return {
    id,
    filename,
    displayName,
    fileType: fileType as DocItem['fileType'],
    fileSize,
    createdAt,
    updatedAt,
    note: typeof value.note === 'string' ? value.note : '',
    sourcePath: typeof value.sourcePath === 'string' ? value.sourcePath : '',
    textPath: typeof value.textPath === 'string' ? value.textPath : '',
  };
}

export const useDocumentStore = defineStore('document-store', {
  state: (): DocumentState => ({
    documents: [],
    loading: false,
    error: null,
    socketBound: false,
    socketUnsubscribers: [],
  }),
  actions: {
    bindSocketEvents(): void {
      if (this.socketBound) {
        return;
      }

      const unbindOnConnected = on('socket:connected', () => {
        void this.getAllDocuments().catch(() => undefined);
      });
      const unbindOnCreated = on('document:created', (payload) => {
        this.handleDocumentCreated(payload);
      });
      const unbindOnRemoved = on('document:removed', (payload) => {
        this.handleDocumentRemoved(payload);
      });

      this.socketUnsubscribers = [unbindOnConnected, unbindOnCreated, unbindOnRemoved];
      this.socketBound = true;
    },

    unbindSocketEvents(): void {
      for (const unsubscribe of this.socketUnsubscribers) {
        unsubscribe();
      }

      this.socketUnsubscribers = [];
      this.socketBound = false;
    },

    addDocumentToStore(doc: DocItem): void {
      const existingIndex = this.documents.findIndex((existingDoc) => existingDoc.id === doc.id);
      if (existingIndex >= 0) {
        this.documents.splice(existingIndex, 1, doc);
        return;
      }

      this.documents.unshift(doc);
    },

    replaceDocument(tempId: string, doc: DocItem): void {
      const targetIndex = this.documents.findIndex((existingDoc) => existingDoc.id === tempId);
      if (targetIndex >= 0) {
        this.documents.splice(targetIndex, 1, doc);
        return;
      }

      this.addDocumentToStore(doc);
    },

    removeDocumentFromStore(id: string): void {
      this.documents = this.documents.filter((doc) => doc.id !== id);
    },

    handleDocumentCreated(payload: unknown): void {
      if (!isRecord(payload)) {
        return;
      }

      const tempId = toNonEmptyString(payload.tempId);
      const candidate = toDocItemFromCreatedPayload(payload)
        ?? toDocItemFromCreatedPayload(payload.doc)
        ?? toDocItemFromCreatedPayload(payload.document);

      if (!candidate) {
        return;
      }

      if (tempId) {
        this.replaceDocument(tempId, candidate);
        return;
      }

      this.addDocumentToStore(candidate);
    },

    handleDocumentRemoved(payload: unknown): void {
      if (!isRecord(payload)) {
        return;
      }

      const removedId = toNonEmptyString(payload.id);
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
        this.addDocumentToStore(doc);
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
