<script setup lang="ts">
import { computed } from 'vue'
// components
import LastSentence from '@/components/DocumentDetail/SentenceTable/LastSentence.vue'
import SentenceList from '@/components/DocumentDetail/SentenceTable/SentenceList.vue'
import Pagination from '@/components/DocumentDetail/SentenceTable/Pagination.vue'
// stores
import { useSentenceStore } from '@/stores/sentenceStore'

const sentenceStore = useSentenceStore();
const sentenceList = computed(() => sentenceStore.sentenceList)

</script>

<template>
  <section class="min-h-0 flex flex-1 flex-col overflow-hidden bg-background-elevated/15">
    <LastSentence v-if="sentenceList.prevSentence" />

    <main data-sentence-scroll-area
      class="min-h-0 flex-1 overflow-y-auto p-2">
      <SentenceList />
    </main>

    <Pagination />
</section>
</template>
