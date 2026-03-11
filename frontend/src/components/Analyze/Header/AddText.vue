<script setup lang="ts">
import { Plus } from 'lucide-vue-next'
import { storeToRefs } from 'pinia'

import { useDocumentStore } from '@/stores/documentStore'

const documentStore = useDocumentStore()
const { loading } = storeToRefs(documentStore)

async function openFilePicker(): Promise<void> {
  if (loading.value) {
    return
  }

  if (!window.electronAPI?.selectDocumentFile) {
    documentStore.error = 'Electron file picker unavailable. Start with npm run electron:dev.'
    return
  }

  try {
    const filePath = await window.electronAPI.selectDocumentFile()
    if (!filePath) {
      return
    }

    await documentStore.addDocumentByPath(filePath)
  } catch {
    // store handles error state
  }
}
</script>

<template>
  <div class="absolute inset-0 pointer-events-none">
    <div class="absolute right-6 top-1/2 z-20 -translate-y-1/2 pointer-events-auto">
      <button type="button"
        class="inline-flex h-10 w-10 items-center justify-center rounded-full border-0 bg-contrast p-0 text-primary shadow-md transition hover:bg-secondary-soft hover:text-primary"
        :disabled="loading"
        aria-label="Add text file"
        title="Add text file"
        @click="openFilePicker">
        <Plus class="h-5 w-5 shrink-0" />
      </button>
    </div>
  </div>
</template>
