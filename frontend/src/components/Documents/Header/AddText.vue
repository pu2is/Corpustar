<script setup lang="ts">
import { Plus } from 'lucide-vue-next'
import { ref } from 'vue'

import { useDocumentStore } from '@/stores/documentStore'

const documentStore = useDocumentStore()
const submitting = ref(false)

async function openFilePicker(): Promise<void> {
  if (submitting.value) {
    return
  }

  if (!window.electronAPI?.selectDocumentFile) {
    return
  }

  submitting.value = true
  try {
    const filePath = await window.electronAPI.selectDocumentFile()
    if (!filePath) {
      return
    }

    await documentStore.addDocumentByPath(filePath)
  } catch {
    // request failed
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="absolute inset-0 pointer-events-none">
    <div class="absolute right-6 top-1/2 z-20 -translate-y-1/2 pointer-events-auto">
      <button type="button"
        class="inline-flex cursor-pointer h-10 w-10 items-center justify-center rounded-full border-0 bg-contrast p-0 text-primary shadow-md transition hover:bg-secondary-soft hover:text-primary"
        :disabled="submitting"
        aria-label="Add text file"
        title="Add text file"
        @click="openFilePicker">
        <Plus class="h-5 w-5 shrink-0" />
      </button>
    </div>
  </div>
</template>
