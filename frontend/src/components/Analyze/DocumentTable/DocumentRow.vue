<script setup lang="ts">
import { computed } from 'vue'
import { ChevronRight, Trash2 } from 'lucide-vue-next'

import type { DocItem } from '@/types/documents'
import { formatFileSize } from '@/utils/utils'

const props = defineProps<{
  docItem: DocItem
}>()
const emit = defineEmits<{
  remove: [id: string]
}>()

const displayName = computed(() => props.docItem.displayName.trim() || props.docItem.filename)
const fileSizeLabel = computed(() => formatFileSize(props.docItem.fileSize))

function removeDocument(event: MouseEvent): void {
  event.stopPropagation()
  emit('remove', props.docItem.id)
}
</script>

<template>
  <div class="cursor-pointer bg-background-elevated/60 text-[0.84rem] font-medium text-text-muted transition-colors hover:bg-background-elevated">
    <div class="flex items-center justify-between gap-3">
      <div class="p-4">
        <div>{{ displayName }}</div>
        <div class="mt-0.5 text-[0.72rem] font-normal text-text-muted/80">
          {{ fileSizeLabel }}
        </div>
      </div>
      <div class="mr-4 flex items-center gap-2">
        <button type="button"
          class="inline-flex items-center cursor-pointer justify-center rounded p-1 text-text-muted/70 transition-colors hover:text-error"
          aria-label="Delete document"
          @click="removeDocument">
          <Trash2 class="h-4 w-4 shrink-0" />
        </button>
        <ChevronRight class="h-4 w-4 shrink-0 text-text-muted/70" />
      </div>
    </div>
  </div>
</template>
