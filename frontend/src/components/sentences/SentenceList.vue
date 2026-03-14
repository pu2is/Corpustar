<script setup lang="ts">
import SentenceListItem from '@/components/sentences/SentenceListItem.vue'
import type { ProcessingItem } from '@/types/processings'
import type { SentenceItem } from '@/types/sentences'

const props = defineProps<{
  processing: ProcessingItem | null
  items: SentenceItem[]
  selectedSentenceIds: string[]
  hasMore: boolean
  loading: boolean
}>()

const emit = defineEmits<{
  toggleSelect: [sentenceId: string]
  clip: [sentenceId: string, splitOffset: number]
  loadMore: []
}>()
</script>

<template>
  <section v-if="props.processing"
    class="min-h-0 flex flex-1 flex-col gap-2">
    <p
      v-if="!items.length"
      class="text-sm text-text-muted"
    >
      No sentences in this segmentation result.
    </p>

    <div
      v-else
      class="scroll-area min-h-0 flex-1 overflow-y-auto pr-1"
    >
      <ul class="space-y-2">
        <SentenceListItem
          v-for="item in props.items"
          :key="item.id"
          :item="item"
          :selected="props.selectedSentenceIds.includes(item.id)"
          :loading="props.loading"
          @toggle-select="(sentenceId) => emit('toggleSelect', sentenceId)"
          @clip="(sentenceId, splitOffset) => emit('clip', sentenceId, splitOffset)"
        />
      </ul>
    </div>

    <button
      v-if="props.hasMore"
      type="button"
      :disabled="props.loading"
      class="shrink-0 rounded border px-3 py-1 text-sm disabled:opacity-60"
      @click="emit('loadMore')"
    >
      Load More
    </button>
  </section>
</template>
