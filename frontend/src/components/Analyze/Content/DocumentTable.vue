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
  <section class="flex flex-col gap-3">
    <header class="flex items-end justify-between gap-3">
      <div>
        <h2 class="m-0 text-[0.95rem] font-semibold tracking-[0.01em] text-text">
          Documents
        </h2>
        <p class="mt-0.5 text-xs text-text-muted">
          {{ documentCount }} item{{ documentCount === 1 ? '' : 's' }}
        </p>
      </div>

      <button
        type="button"
        class="min-w-26 rounded-full border border-border-soft bg-background px-3.5 py-1.5 text-xs font-semibold text-text shadow-none hover:bg-background-elevated disabled:cursor-wait disabled:opacity-75"
        :disabled="loading"
        @click="refreshDocuments"
      >
        {{ loading ? 'Refreshing...' : 'Refresh' }}
      </button>
    </header>

    <p
      v-if="error"
      class="m-0 rounded-xl border border-error/30 bg-error-soft/30 px-4 py-3 text-sm text-error"
    >
      {{ error }}
    </p>

    <p
      v-else-if="loading && !hasDocuments"
      class="m-0 rounded-xl border border-border-soft bg-background px-4 py-3 text-sm text-text-muted"
    >
      Loading documents...
    </p>

    <p
      v-else-if="!hasDocuments"
      class="m-0 rounded-xl border border-border-soft bg-background px-4 py-3 text-sm text-text-muted"
    >
      No documents found.
    </p>

    <div v-else class="overflow-hidden rounded-xl border border-border-soft bg-background">
      <div class="overflow-auto">
        <table class="w-full min-w-[760px] border-collapse">
          <thead>
            <tr>
              <th
                scope="col"
                class="sticky top-0 z-10 border-b border-border-soft bg-background-elevated px-4 py-3 text-left text-[11px] uppercase tracking-[0.06em] text-text-muted"
              >
                Name
              </th>
              <th
                scope="col"
                class="sticky top-0 z-10 border-b border-border-soft bg-background-elevated px-4 py-3 text-left text-[11px] uppercase tracking-[0.06em] text-text-muted"
              >
                Type
              </th>
              <th
                scope="col"
                class="sticky top-0 z-10 border-b border-border-soft bg-background-elevated px-4 py-3 text-left text-[11px] uppercase tracking-[0.06em] text-text-muted"
              >
                Size
              </th>
              <th
                scope="col"
                class="sticky top-0 z-10 border-b border-border-soft bg-background-elevated px-4 py-3 text-left text-[11px] uppercase tracking-[0.06em] text-text-muted"
              >
                Updated
              </th>
              <th
                scope="col"
                class="sticky top-0 z-10 border-b border-border-soft bg-background-elevated px-4 py-3 text-left text-[11px] uppercase tracking-[0.06em] text-text-muted"
              >
                Source Path
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="document in documents"
              :key="document.id"
              class="transition-colors hover:bg-background-elevated [&:last-child_td]:border-b-0"
            >
              <td class="border-b border-border-soft px-4 py-3 text-[0.84rem] font-semibold text-text">
                {{ readDisplayName(document) }}
              </td>
              <td class="border-b border-border-soft px-4 py-3 text-[12px] uppercase tracking-[0.04em] text-text">
                {{ formatFileType(document.fileType) }}
              </td>
              <td class="border-b border-border-soft px-4 py-3 text-[0.84rem] text-text">
                {{ formatFileSize(document.fileSize) }}
              </td>
              <td class="border-b border-border-soft px-4 py-3 text-[0.84rem] text-text">
                {{ formatDate(document.updatedAt) }}
              </td>
              <td
                class="max-w-[28rem] truncate border-b border-border-soft px-4 py-3 font-mono text-[12px] text-text-muted"
                :title="document.sourcePath"
              >
                {{ document.sourcePath }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>
