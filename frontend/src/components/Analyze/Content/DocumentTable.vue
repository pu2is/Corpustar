<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'

import { useDocumentStore } from '@/stores/documentStore'
import type { DocItem } from '@/types/documents'

const documentStore = useDocumentStore()
const { documents, loading, error } = storeToRefs(documentStore)

const hasDocuments = computed(() => documents.value.length > 0)
const documentCount = computed(() => documents.value.length)

onMounted(() => {
  if (!documents.value.length && !loading.value) {
    void documentStore.getAllDocuments()
  }
})

function refreshDocuments(): void {
  void documentStore.getAllDocuments()
}

function readDisplayName(document: DocItem): string {
  return document.displayName.trim() || document.filename
}

function formatFileType(fileType: DocItem['fileType']): string {
  return fileType.toUpperCase()
}

function formatFileSize(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) {
    return '-'
  }

  if (bytes < 1024) {
    return `${bytes} B`
  }

  const units = ['KB', 'MB', 'GB', 'TB']
  let size = bytes / 1024
  let unitIndex = 0

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex += 1
  }

  return `${size.toFixed(size >= 100 ? 0 : 1)} ${units[unitIndex]}`
}

function formatDate(dateValue: string): string {
  const parsed = new Date(dateValue)
  if (Number.isNaN(parsed.getTime())) {
    return '-'
  }

  return parsed.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <section class="document-table">
    <header class="table-header">
      <div>
        <h2 class="table-title">
          Documents
        </h2>
        <p class="table-meta">
          {{ documentCount }} item{{ documentCount === 1 ? '' : 's' }}
        </p>
      </div>

      <button
        type="button"
        class="refresh-button"
        :disabled="loading"
        @click="refreshDocuments"
      >
        {{ loading ? 'Refreshing...' : 'Refresh' }}
      </button>
    </header>

    <p v-if="error" class="table-state table-state-error">
      {{ error }}
    </p>

    <p v-else-if="loading && !hasDocuments" class="table-state">
      Loading documents...
    </p>

    <p v-else-if="!hasDocuments" class="table-state">
      No documents found.
    </p>

    <div v-else class="table-shell">
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">
                Name
              </th>
              <th scope="col">
                Type
              </th>
              <th scope="col">
                Size
              </th>
              <th scope="col">
                Updated
              </th>
              <th scope="col">
                Source Path
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="document in documents" :key="document.id">
              <td class="cell-name">
                {{ readDisplayName(document) }}
              </td>
              <td class="cell-type">
                {{ formatFileType(document.fileType) }}
              </td>
              <td>
                {{ formatFileSize(document.fileSize) }}
              </td>
              <td>
                {{ formatDate(document.updatedAt) }}
              </td>
              <td class="cell-path" :title="document.sourcePath">
                {{ document.sourcePath }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<style scoped>
.document-table {
  --table-border: color-mix(in srgb, var(--color-border) 55%, transparent);
  --table-border-soft: color-mix(in srgb, var(--color-border-soft) 70%, white);
  --table-surface: color-mix(in srgb, var(--color-background) 84%, white);
  --table-surface-head: color-mix(in srgb, var(--color-background-elevated) 65%, white);
  --table-hover: color-mix(in srgb, var(--color-primary-soft) 30%, white);
  --table-radius: 12px;
  --table-padding-x: 0.9rem;
  --table-padding-y: 0.72rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.table-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 0.75rem;
}

.table-title {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 650;
  letter-spacing: 0.01em;
}

.table-meta {
  margin: 0.1rem 0 0;
  font-size: 0.78rem;
  color: var(--page-muted);
}

.refresh-button {
  min-width: 6.5rem;
  border-radius: 999px;
  border: 1px solid var(--table-border);
  padding: 0.45rem 0.85rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-text);
  background: var(--table-surface);
  box-shadow: none;
}

.refresh-button:disabled {
  cursor: wait;
  opacity: 0.75;
}

.table-state {
  margin: 0;
  border: 1px solid var(--table-border-soft);
  border-radius: var(--table-radius);
  padding: 0.9rem 1rem;
  font-size: 0.85rem;
  color: var(--page-muted);
  background: var(--table-surface);
}

.table-state-error {
  color: var(--color-error);
  border-color: color-mix(in srgb, var(--color-error) 30%, transparent);
  background: color-mix(in srgb, var(--color-error-soft) 30%, white);
}

.table-shell {
  border: 1px solid var(--table-border-soft);
  border-radius: var(--table-radius);
  background: var(--table-surface);
  overflow: hidden;
}

.table-scroll {
  overflow: auto;
}

table {
  width: 100%;
  min-width: 760px;
  border-collapse: collapse;
}

th,
td {
  text-align: left;
  padding: var(--table-padding-y) var(--table-padding-x);
  border-bottom: 1px solid var(--table-border-soft);
  vertical-align: middle;
  font-size: 0.84rem;
}

th {
  position: sticky;
  top: 0;
  z-index: 1;
  font-size: 0.72rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--page-muted);
  background: var(--table-surface-head);
}

tbody tr:last-child td {
  border-bottom: 0;
}

tbody tr:hover {
  background: var(--table-hover);
}

.cell-name {
  font-weight: 600;
}

.cell-type {
  font-variant: all-small-caps;
  letter-spacing: 0.04em;
}

.cell-path {
  max-width: 28rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.8rem;
  color: var(--page-muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
</style>
