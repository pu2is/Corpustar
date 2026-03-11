<script setup lang="ts">
import { Plus } from 'lucide-vue-next'
import { ref } from 'vue'

const emit = defineEmits<{
  (e: 'file-selected', file: File): void
}>()

const fileInput = ref<HTMLInputElement | null>(null)
const acceptedFileTypes = '.doc,.docx,.txt,.odt'

function openFilePicker(): void {
  fileInput.value?.click()
}

function handleFileChange(event: Event): void {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) {
    return
  }

  emit('file-selected', file)
  input.value = ''
}
</script>

<template>
  <div class="absolute right-6 top-1/2 z-10 -translate-y-1/2">
    <input ref="fileInput"
      type="file"
      class="hidden"
      :accept="acceptedFileTypes"
      @change="handleFileChange" />
    <button type="button"
      class="inline-flex h-10 w-10 items-center justify-center rounded-full border-0 bg-contrast p-0 text-primary shadow-md transition hover:bg-secondary-soft hover:text-primary"
      aria-label="Add text file"
      title="Add text file"
      @click="openFilePicker">
      <Plus class="h-5 w-5 shrink-0" />
    </button>
  </div>
</template>
