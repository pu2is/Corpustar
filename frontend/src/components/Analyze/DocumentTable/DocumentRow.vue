<script setup lang="ts">
import { computed } from 'vue'
import { ChevronRight } from 'lucide-vue-next'

import type { DocItem } from '@/types/documents'
import { formatFileSize } from '@/utils/utils'

const props = defineProps<{
  docItem: DocItem
}>()

const displayName = computed(() => props.docItem.displayName.trim() || props.docItem.filename)
const fileSizeLabel = computed(() => formatFileSize(props.docItem.fileSize))
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
      <ChevronRight class="mr-4 h-4 w-4 shrink-0 text-text-muted/70" />
    </div>
  </div>
</template>
