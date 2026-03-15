<script setup lang="ts">
import { ref } from 'vue'

import ClipSentenceDialog from '@/components/DocumentDetail/Content/SentenceSegmentation/ClipSentenceDialog.vue'
import type { SentenceItem } from '@/types/sentences'

type MergeDirection = 'prev' | 'next'

const props = defineProps<{
  item: SentenceItem
  loading: boolean
  canMergePrev: boolean
  canMergeNext: boolean
}>()

const emit = defineEmits<{
  requestMerge: [sentenceId: string, direction: MergeDirection]
  clip: [sentenceId: string, splitOffset: number]
}>()

const clipDialogOpen = ref(false)

function requestMerge(direction: MergeDirection): void {
  emit('requestMerge', props.item.id, direction)
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
      <div class="min-w-0 flex-1 space-y-1">
        <p class="text-xs text-text-muted">
          {{ item.startOffset }} - {{ item.endOffset }}
        </p>
        <p class="text-sm whitespace-pre-wrap break-words">
          {{ item.text }}
        </p>
      </div>
    </div>
    <div class="flex gap-2">
      <button type="button"
        :disabled="loading || !canMergePrev"
        class="rounded border px-2 py-1 text-xs disabled:opacity-60"
        @click="requestMerge('prev')">
        Merge Prev
      </button>
      <button type="button"
        :disabled="loading || !canMergeNext"
        class="rounded border px-2 py-1 text-xs disabled:opacity-60"
        @click="requestMerge('next')">
        Merge Next
      </button>
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
