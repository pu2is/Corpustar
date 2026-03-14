<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute, useRouter } from 'vue-router'

import TopNav from '@/components/Nav/TopNav.vue'
import SentenceList from '@/components/sentences/SentenceList.vue'
import SentenceToolbar from '@/components/sentences/SentenceToolbar.vue'
import { useDocumentStore } from '@/stores/documentStore'
import { useSentenceStore } from '@/stores/sentenceStore'
import { BookOpenText, ChevronLeft } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const documentStore = useDocumentStore()
const sentenceStore = useSentenceStore()

const { documents } = storeToRefs(documentStore)
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
const sourceTextPath = computed(() => {
  if (activeProcessing.value) {
    return ''
  }
  return documentItem.value?.textPath ?? ''
})
const pageLoading = ref(false)
const sourceText = ref('')
const sourceTextLoading = ref(false)
const sourceTextError = ref<string | null>(null)
let initializeRequestId = 0
let textRequestId = 0

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

async function initializeAnalyzeWorkspace(targetDocId: string): Promise<void> {
  const requestId = ++initializeRequestId
  pageLoading.value = true

  try {
    const hasDocumentInStore = documents.value.some((doc) => doc.id === targetDocId)
    if (!hasDocumentInStore) {
      await documentStore.getAllDocuments()
    }

    await sentenceStore.initializeAnalyzePage(targetDocId)
  } catch {
    // Store actions already preserve error state for rendering.
  } finally {
    if (requestId === initializeRequestId) {
      pageLoading.value = false
    }
  }
}

async function loadSourceText(textPath: string): Promise<void> {
  const requestId = ++textRequestId
  sourceTextLoading.value = true
  sourceTextError.value = null

  try {
    if (!window.electronAPI?.readDocumentText) {
      throw new Error('Document text reader unavailable. Start with npm run electron:dev.')
    }

    const content = await window.electronAPI.readDocumentText(textPath)
    if (requestId === textRequestId) {
      sourceText.value = content
    }
  } catch (error) {
    if (requestId === textRequestId) {
      sourceText.value = ''
      sourceTextError.value = error instanceof Error ? error.message : String(error)
    }
  } finally {
    if (requestId === textRequestId) {
      sourceTextLoading.value = false
    }
  }
}

watch(
  docId,
  (nextDocId) => {
    if (!nextDocId) {
      pageLoading.value = false
      return
    }
    void initializeAnalyzeWorkspace(nextDocId)
  },
  { immediate: true },
)

watch(
  sourceTextPath,
  (nextTextPath) => {
    if (!nextTextPath) {
      sourceText.value = ''
      sourceTextLoading.value = false
      sourceTextError.value = null
      return
    }

    void loadSourceText(nextTextPath)
  },
  { immediate: true },
)

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
    <div class="min-h-0 flex flex-1 flex-col overflow-hidden px-16 ml-16 p-6">
      <button type="button"
        class="mb-4 inline-flex shrink-0 cursor-pointer items-center gap-2 text-sm font-medium text-text-muted transition-colors hover:text-text"
        @click="backToDocuments">
        <ChevronLeft class="h-4 w-4" />
        Back to documents
      </button>

      <p v-if="pageLoading"
        class="text-sm text-text-muted">
        Loading...
      </p>

      <section v-else-if="documentItem"
        class="min-h-0 flex flex-1 flex-col gap-3">

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

        <section class="min-h-0 flex flex-1 flex-col gap-3 overflow-hidden rounded border border-border p-3">
          <SentenceToolbar
            :processing="activeProcessing"
            :loading="sentenceLoading"
            :can-merge="canMerge"
            class="shrink-0"
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
            v-if="activeProcessing"
            :processing="activeProcessing"
            :items="sentenceItems"
            :selected-sentence-ids="selectedSentenceIds"
            :has-more="sentenceHasMore"
            :loading="sentenceLoading"
            class="min-h-0 flex-1"
            @toggle-select="toggleSentenceSelection"
            @clip="clipSentence"
            @load-more="loadMoreSentences"
          />

          <section v-else
            class="min-h-0 flex flex-1 flex-col overflow-hidden rounded border border-border/60 bg-background-elevated/25 p-3">
            <p v-if="sourceTextLoading"
              class="text-sm text-text-muted">
              Loading full text...
            </p>
            <p v-else-if="sourceTextError"
              class="text-sm text-error">
              {{ sourceTextError }}
            </p>
            <div v-else
              class="scroll-area min-h-0 flex-1 overflow-y-auto pr-1">
              <p class="text-sm whitespace-pre-wrap break-words text-text">
                {{ sourceText || 'This document has no text content.' }}
              </p>
            </div>
          </section>
        </section>
      </section>

      <section v-else
        class="space-y-2">
        <p class="text-sm text-text-muted">
          Document not found.
        </p>
      </section>
    </div>
  </section>
</template>
