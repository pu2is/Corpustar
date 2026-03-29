<script setup lang="ts">
import { computed } from 'vue'
import LemmatizationTable from '@/components/DocumentDetailOld/Content/Lemmatization/LemmatizationTable.vue'
import { useLemmatizationTable } from '@/composables/documentDetail/useLemmatizationTable'

const props = defineProps<{
  docId: string
}>()

const {
  hasLemmatizeProcess,
  lemmaItems,
  currentPage,
  hasPreviousPage,
  hasNextPage,
  pageLoading,
  showLemmaLoading,
  goToPreviousPage,
  goToNextPage,
} = useLemmatizationTable(computed(() => props.docId))
</script>

<template>
  <div class="min-h-0 flex flex-1 flex-col gap-3 overflow-hidden">
    <p
      v-if="showLemmaLoading"
      class="text-sm text-text-muted">
      Loading lemmas...
    </p>

    <p
      v-else-if="!hasLemmatizeProcess"
      class="text-sm text-text-muted">
      Lemmatization result is not ready yet.
    </p>

    <p
      v-else-if="lemmaItems.length === 0"
      class="text-sm text-text-muted">
      No lemmas available for this page.
    </p>

    <LemmatizationTable
      v-else
      :items="lemmaItems"
      :current-page="currentPage"
      :has-previous="hasPreviousPage"
      :has-next="hasNextPage"
      :loading="pageLoading"
      @previous="goToPreviousPage"
      @next="goToNextPage" />
  </div>
</template>
