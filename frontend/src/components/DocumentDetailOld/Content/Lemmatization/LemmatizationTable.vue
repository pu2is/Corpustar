<script setup lang="ts">
import SentencePagination from '@/components/DocumentDetailOld/Content/SentencePagination.vue'
import LemmaPairItem from '@/components/DocumentDetailOld/Content/Lemmatization/LemmaPairItem.vue'
import type { LemmaViewItem } from '@/types/lemmatize'

const props = defineProps<{
  items: LemmaViewItem[]
  currentPage: number
  hasPrevious: boolean
  hasNext: boolean
  loading: boolean
}>()

const emit = defineEmits<{
  previous: []
  next: []
}>()
</script>

<template>
  <div class="min-h-0 flex flex-1 flex-col overflow-hidden bg-background-elevated/15">
    <div class="scroll-area min-h-0 flex-1 overflow-y-auto">
      <div class="space-y-2">
        <LemmaPairItem v-for="item in props.items"
          :key="item.id"
          :item="item" />
      </div>
    </div>

    <SentencePagination :current-page="props.currentPage"
      :item-count="props.items.length" :has-previous="props.hasPrevious"
      :has-next="props.hasNext" :loading="props.loading"
      @previous="emit('previous')" @next="emit('next')" />
  </div>
</template>
