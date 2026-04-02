<script setup lang="ts">
import { computed } from 'vue'
// components
import LastSentence from '@/components/DocumentDetail/SentenceTable/LastSentence.vue'
import SentenceList from '@/components/DocumentDetail/SentenceTable/SentenceList.vue'
import Pagination from '@/components/DocumentDetail/SentenceTable/Pagination.vue'
// stores
import { useSentenceStore } from '@/stores/sentenceStore'

const sentenceStore = useSentenceStore();
const isFirstPage = computed(() => sentenceStore.sentenceList.prevSentence === null)
const lastSentenceText = computed(() => sentenceStore.sentenceList.prevSentence?.source_text ?? '')
</script>

<template>
  <section class="min-h-0 flex flex-1 flex-col overflow-hidden bg-background-elevated/15">
    <LastSentence v-if="!isFirstPage"
      :last-sentence-text="lastSentenceText" />
    <main class="min-h-0 flex-1 overflow-y-auto p-2">
      <SentenceList />
    </main>
    <Pagination />
  </section>
</template>
