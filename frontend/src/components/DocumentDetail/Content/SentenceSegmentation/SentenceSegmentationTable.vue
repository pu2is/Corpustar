<script setup lang="ts">
import { computed, ref } from 'vue'
import LastSentenceItem from '@/components/DocumentDetail/Content/LastSentenceItem.vue'
import SentencePagination from '@/components/DocumentDetail/Content/SentencePagination.vue'
import SentencesOfDocument from '@/components/DocumentDetail/Content/SentenceSegmentation/SentencesOfDocument.vue'
import type { SentenceItem } from '@/types/sentences'

const props = defineProps<{
  items: SentenceItem[]
  lastSentenceItem: SentenceItem | null
  lastSentenceLoading: boolean
  currentPage: number
  hasPrevious: boolean
  hasNext: boolean
  tableLoading: boolean
  sentenceActionLoading: boolean
  highlightedSentenceIds: string[]
}>()

const emit = defineEmits<{
  previous: []
  next: []
  requestMerge: [sentenceId: string]
  clip: [sentenceId: string, splitOffset: number]
}>()

const highlightedSentenceIdSet = computed(() => new Set(props.highlightedSentenceIds))
const scrollAreaRef = ref<HTMLDivElement | null>(null)

function handleRequestMerge(sentenceId: string): void {
  emit('requestMerge', sentenceId)
}

function handleClip(sentenceId: string, splitOffset: number): void {
  emit('clip', sentenceId, splitOffset)
}

function getScrollAreaElement(): HTMLDivElement | null {
  return scrollAreaRef.value
}

defineExpose({
  getScrollAreaElement,
})
</script>

<template>
  <div class="min-h-0 flex flex-1 flex-col overflow-hidden bg-background-elevated/15">
    <div
      ref="scrollAreaRef"
      class="scroll-area min-h-0 flex-1 overflow-y-auto">
      <LastSentenceItem
        :item="props.lastSentenceItem"
        :loading="props.sentenceActionLoading || props.lastSentenceLoading" />

      <div class="space-y-2">
        <SentencesOfDocument
          v-for="(item, index) in props.items"
          :key="item.id"
          :item="item"
          :loading="props.tableLoading"
          :can-merge-prev="index > 0 || (index === 0 && item.start_offset > 0 && props.lastSentenceItem !== null)"
          :highlighted="highlightedSentenceIdSet.has(item.id)"
          :allow-sentence-actions="true"
          @request-merge="handleRequestMerge"
          @clip="handleClip" />
      </div>
    </div>

    <SentencePagination
      :current-page="props.currentPage"
      :item-count="props.items.length"
      :has-previous="props.hasPrevious"
      :has-next="props.hasNext"
      :loading="props.tableLoading"
      @previous="emit('previous')"
      @next="emit('next')" />
  </div>
</template>
