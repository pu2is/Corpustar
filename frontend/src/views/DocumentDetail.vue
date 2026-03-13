<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute, useRouter } from 'vue-router'

import TopNav from '@/components/Nav/TopNav.vue'
import ProcessingStatusBar from '@/components/sentences/ProcessingStatusBar.vue'
import SentenceList from '@/components/sentences/SentenceList.vue'
import SentenceToolbar from '@/components/sentences/SentenceToolbar.vue'
import { useDocumentStore } from '@/stores/documentStore'
import { useSentenceStore } from '@/stores/sentenceStore'
import { BookOpenText, ChevronLeft } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const documentStore = useDocumentStore()
const sentenceStore = useSentenceStore()

const { documents, loading } = storeToRefs(documentStore)
const {
  errorByDocId,
  hasMoreByDocId,
  itemsByDocId,
  loadingByDocId,
  processingByDocId,
  selectedSentenceIdsByDocId,
} = storeToRefs(sentenceStore)

const docId = computed(() => {
  const value = route.params.doc_id
  return typeof value === 'string' ? value : ''
})

const documentItem = computed(() => documents.value.find((doc) => doc.id === docId.value) ?? null)
const formattedCharCount = computed(() => (documentItem.value?.textCharCount ?? 0).toLocaleString())

const activeProcessing = computed(() => processingByDocId.value[docId.value] ?? null)
const sentenceItems = computed(() => itemsByDocId.value[docId.value] ?? [])
const sentenceHasMore = computed(() => hasMoreByDocId.value[docId.value] ?? false)
const sentenceLoading = computed(() => loadingByDocId.value[docId.value] ?? false)
const selectedSentenceIds = computed(() => selectedSentenceIdsByDocId.value[docId.value] ?? [])
const sentenceError = computed(() => errorByDocId.value[docId.value] ?? null)
const canMerge = computed(() => selectedSentenceIds.value.length >= 2)

function segmentSentences(): void {
  if (!docId.value) {
    return
  }
  void sentenceStore.segmentDocument(docId.value).catch(() => undefined)
}

function mergeSelectedSentences(): void {
  if (!docId.value) {
    return
  }
  void sentenceStore.mergeSelected(docId.value).catch(() => undefined)
}

function loadMoreSentences(): void {
  if (!docId.value || !activeProcessing.value) {
    return
  }
  void sentenceStore
    .loadMoreSentences(docId.value, activeProcessing.value.id)
    .catch(() => undefined)
}

function toggleSentenceSelection(sentenceId: string): void {
  if (!docId.value) {
    return
  }
  sentenceStore.toggleSentenceSelection(docId.value, sentenceId)
}

function clipSentence(sentenceId: string, splitOffset: number): void {
  if (!docId.value) {
    return
  }
  void sentenceStore.clipSentence(docId.value, sentenceId, splitOffset).catch(() => undefined)
}

onMounted(() => {
  if (!documents.value.length && !loading.value) {
    void documentStore.getAllDocuments()
  }
})

function backToDocuments(): void {
  void router.push('/analyze')
}
</script>

<template>
  <section class="-mx-16 flex h-full flex-col overflow-hidden">
    <header class="relative flex min-h-16 items-center justify-between gap-4 bg-primary px-6 py-4 text-contrast shadow-sm">
      <TopNav />
    </header>

    <!-- Content Header -->
    <div class="scroll-area min-h-0 flex-1 px-16 ml-16 overflow-y-auto p-6">
      <button type="button"
        class="mb-4 cursor-pointer inline-flex items-center gap-2 text-sm font-medium text-text-muted transition-colors hover:text-text"
        @click="backToDocuments">
        <ChevronLeft class="h-4 w-4" />
        Back to documents
      </button>

      <section v-if="documentItem"
        class="space-y-3">

        <header class="rounded border border-border p-3 space-y-1">
          <div class="flex flex-wrap items-center gap-3">
            <h2 class="text-xl font-semibold text-text">
              {{ documentItem.displayName }}
            </h2>
          </div>
          <!-- Doc Info -->
          <div class="flex items gap-4">
            <span class="inline-flex items-center gap-2 py-1 text-xs text-text-muted">
              <BookOpenText class="h-3.5 w-3.5" />
              {{ formattedCharCount }} characters
            </span>
            <span class="inline-flex items-center gap-2 py-1 text-xs text-text-muted">
              id: {{ documentItem.id }}
            </span>
          </div>
        </header>

        <section class="space-y-3 rounded border border-border p-3">
          <ProcessingStatusBar :processing="activeProcessing" />

          <SentenceToolbar
            :loading="sentenceLoading"
            :can-merge="canMerge"
            @segment="segmentSentences"
            @merge="mergeSelectedSentences"
          />

          <p
            v-if="sentenceError"
            class="text-sm text-error"
          >
            {{ sentenceError }}
          </p>

          <SentenceList
            :items="sentenceItems"
            :selected-sentence-ids="selectedSentenceIds"
            :has-more="sentenceHasMore"
            :loading="sentenceLoading"
            @toggle-select="toggleSentenceSelection"
            @clip="clipSentence"
            @load-more="loadMoreSentences"
          />
        </section>
      </section>

      <section v-else
        class="space-y-3 animate-pulse"
        aria-busy="true">
        <header class="space-y-2">
          <div class="h-7 w-72 rounded bg-background-elevated/70" />
          <div class="h-4 w-32 rounded bg-background-elevated/70" />
        </header>

        <section class="overflow-hidden rounded border border-border bg-background-elevated/40 p-4 space-y-3">
          <div class="h-4 w-full rounded bg-background-elevated/70" />
          <div class="h-4 w-[96%] rounded bg-background-elevated/70" />
          <div class="h-4 w-[92%] rounded bg-background-elevated/70" />
          <div class="h-4 w-[88%] rounded bg-background-elevated/70" />
          <div class="h-4 w-[84%] rounded bg-background-elevated/70" />
          <div class="h-4 w-[80%] rounded bg-background-elevated/70" />
          <div class="h-4 w-[76%] rounded bg-background-elevated/70" />
        </section>
      </section>
    </div>
  </section>
</template>
