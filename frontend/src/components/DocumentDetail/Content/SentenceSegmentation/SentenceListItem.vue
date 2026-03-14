<script setup lang="ts">
import { ref } from 'vue'

import ClipSentenceDialog from '@/components/DocumentDetail/Content/SentenceSegmentation/ClipSentenceDialog.vue'
import type { SentenceItem } from '@/types/sentences'

const props = defineProps<{
  item: SentenceItem
  selected: boolean
  loading: boolean
}>()

const emit = defineEmits<{
  toggleSelect: [sentenceId: string]
  clip: [sentenceId: string, splitOffset: number]
}>()

const clipDialogOpen = ref(false)

function toggleSelection(): void {
  emit('toggleSelect', props.item.id)
}

function openClipDialog(): void {
  clipDialogOpen.value = true
}

function closeClipDialog(): void {
  clipDialogOpen.value = false
}

function submitClip(splitOffset: number): void {
  emit('clip', props.item.id, splitOffset)
  clipDialogOpen.value = false
}
</script>

<template>
  <div class="rounded border p-2 space-y-2">
    <div class="flex items-start gap-2">
      <input type="checkbox"
        :checked="selected"
        :disabled="loading"
        @change="toggleSelection">
      <div class="min-w-0 flex-1 space-y-1">
        <p class="text-xs text-text-muted">
          {{ item.startOffset }} - {{ item.endOffset }}
        </p>
        <p class="text-sm whitespace-pre-wrap break-words">
          {{ item.text }}
        </p>
      </div>
      <button type="button"
        :disabled="loading"
        class="rounded border px-2 py-1 text-xs disabled:opacity-60"
        @click="openClipDialog">
        Clip
      </button>
    </div>
    <ClipSentenceDialog
      :open="clipDialogOpen"
      @close="closeClipDialog"
      @submit="submitClip"
    />
  </div>
</template>
