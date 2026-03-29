import { computed, nextTick, ref, watch, type Ref } from 'vue'
import { usePaginationStore } from '@/stores/local/paginationStore'
import { useProcessStore } from '@/stores/processStore'
import { useSentenceStore } from '@/stores/sentenceStore'
import type { SentenceItem } from '@/types/sentences'

export function useSentenceSegmentationTable(docId: Ref<string>) {
  const paginationStore = usePaginationStore()
  const processStore = useProcessStore()
  const sentenceStore = useSentenceStore()

  const activeProcessing = computed(() => processStore.getSentenceSegmentationProcessByDocId(docId.value))
  const activeProcessingId = computed(() => activeProcessing.value?.id ?? '')
  const activeDocProcessKey = computed(() => (
    docId.value && activeProcessingId.value ? `${docId.value}::${activeProcessingId.value}` : ''
  ))
  const segmentationState = computed(() => processStore.getSegmentationStateByDocId(docId.value))

  const sentenceItemPerPage = Number.parseInt(import.meta.env.VITE_SENTENCE_ITEM_PER_PAGE ?? '10', 10)
  const lastSentenceItem = ref<SentenceItem | null>(null)
  const lastSentenceLoading = ref(false)
  const highlightedSentenceIds = ref<string[]>([])
  const tableRef = ref<{ getScrollAreaElement: () => HTMLDivElement | null } | null>(null)
  const mutationLoading = ref(false)
  const pendingScrollTop = ref<number | null>(null)
  let lastSentenceRequestToken = 0

  const sentenceItems = computed(() => {
    if (!docId.value || !activeProcessingId.value) {
      return []
    }

    return sentenceStore.getSentenceItems(docId.value, activeProcessingId.value)
  })
  const paginationEntry = computed(() => paginationStore.getPaginationEntry(docId.value, 'sentence'))
  const paginationReady = computed(() => paginationEntry.value.processingId === activeProcessingId.value)
  const pageLoading = computed(() => paginationEntry.value.loading)
  const currentPage = computed(() => paginationEntry.value.currentPage)
  const hasPreviousPage = computed(() => currentPage.value > 1)
  const hasNextPage = computed(() => paginationEntry.value.hasMore)
  const tableLoading = computed(() => pageLoading.value || mutationLoading.value)
  const sentenceActionLoading = computed(() => pageLoading.value || mutationLoading.value)
  const showSegmentationLoading = computed(() => (
    segmentationState.value === 'running'
    || (Boolean(activeProcessingId.value) && (!paginationReady.value || (pageLoading.value && sentenceItems.value.length === 0)))
  ))

  async function loadLastSentenceItem(): Promise<void> {
    const currentDocId = docId.value
    const processingId = activeProcessingId.value
    const firstSentence = sentenceItems.value[0]
    const requestToken = ++lastSentenceRequestToken
    if (!currentDocId || !processingId || !firstSentence
      || firstSentence.start_offset === 0 || currentPage.value <= 1) {
      lastSentenceItem.value = null
      lastSentenceLoading.value = false
      return
    }

    const previousPageOffset = paginationEntry.value.offsets[currentPage.value - 2] ?? null
    lastSentenceLoading.value = true
    lastSentenceItem.value = null

    try {
      const previousPage = await sentenceStore.getSentences(
        currentDocId,
        processingId,
        typeof previousPageOffset === 'number' ? previousPageOffset : null,
        sentenceItemPerPage,
        false,
      )
      if (requestToken !== lastSentenceRequestToken) {
        return
      }

      lastSentenceItem.value = previousPage.items[previousPage.items.length - 1] ?? null
    } catch {
      if (requestToken !== lastSentenceRequestToken) {
        return
      }

      lastSentenceItem.value = null
    } finally {
      if (requestToken === lastSentenceRequestToken) {
        lastSentenceLoading.value = false
      }
    }
  }

  function setHighlightedSentenceIds(sentenceIds: string[]): void {
    highlightedSentenceIds.value = Array.from(new Set(sentenceIds.filter(Boolean)))
  }

  function captureScrollPosition(): void {
    const scrollArea = tableRef.value?.getScrollAreaElement() ?? null
    pendingScrollTop.value = scrollArea && scrollArea.scrollHeight > scrollArea.clientHeight
      ? scrollArea.scrollTop
      : null
  }

  async function restoreScrollPosition(): Promise<void> {
    const scrollTop = pendingScrollTop.value
    if (scrollTop === null) {
      return
    }

    pendingScrollTop.value = null
    await nextTick()
    const scrollArea = tableRef.value?.getScrollAreaElement() ?? null
    if (scrollArea) {
      scrollArea.scrollTop = scrollTop
    }
  }

  function getPreviousSentenceId(sentenceId: string): string | null {
    const sentenceIndex = sentenceItems.value.findIndex((item) => item.id === sentenceId)

    if (sentenceIndex < 0) {
      return null
    }

    if (sentenceIndex > 0) {
      return sentenceItems.value[sentenceIndex - 1]?.id ?? null
    }

    return sentenceItems.value[0]?.start_offset === 0 ? null : lastSentenceItem.value?.id ?? null
  }

  async function goToPreviousPage(): Promise<void> {
    const currentDocId = docId.value
    const processingId = activeProcessingId.value
    if (!currentDocId || !processingId || !hasPreviousPage.value || tableLoading.value) {
      return
    }

    setHighlightedSentenceIds([])
    await paginationStore.goToPreviousPage(currentDocId, processingId, 'sentence')
  }

  async function goToNextPage(): Promise<void> {
    const currentDocId = docId.value
    const processingId = activeProcessingId.value
    if (!currentDocId || !processingId || !hasNextPage.value || tableLoading.value) {
      return
    }

    setHighlightedSentenceIds([])
    await paginationStore.goToNextPage(currentDocId, processingId, 'sentence')
  }

  async function mergePreviousSentence(sentenceId: string): Promise<void> {
    const previousSentenceId = getPreviousSentenceId(sentenceId)
    const currentDocId = docId.value
    const processingId = activeProcessingId.value
    if (!previousSentenceId || !currentDocId || !processingId) {
      return
    }

    captureScrollPosition()
    mutationLoading.value = true
    try {
      const mergedItem = await sentenceStore.mergeSentences([previousSentenceId, sentenceId])
      setHighlightedSentenceIds([mergedItem.id])
      await paginationStore.refreshCurrentPage(currentDocId, processingId, 'sentence')
      await restoreScrollPosition()
    } catch {
      pendingScrollTop.value = null
    } finally {
      mutationLoading.value = false
    }
  }

  async function clipSentence(sentenceId: string, splitOffset: number): Promise<void> {
    const currentDocId = docId.value
    const processingId = activeProcessingId.value
    if (!currentDocId || !processingId) {
      return
    }

    mutationLoading.value = true
    captureScrollPosition()
    try {
      await sentenceStore.clipSentence(sentenceId, splitOffset)
      setHighlightedSentenceIds([])
      await paginationStore.refreshCurrentPage(currentDocId, processingId, 'sentence')
      await restoreScrollPosition()
    } catch {
      pendingScrollTop.value = null
    } finally {
      mutationLoading.value = false
    }
  }

  watch(
    activeDocProcessKey,
    async (nextKey) => {
      highlightedSentenceIds.value = []
      lastSentenceItem.value = null
      lastSentenceLoading.value = false
      pendingScrollTop.value = null
      if (!nextKey || !docId.value || !activeProcessingId.value) {
        return
      }

      await paginationStore.initializeDocumentPagination(docId.value, activeProcessingId.value, 'sentence')
    },
    { immediate: true },
  )

  watch(
    [
      activeDocProcessKey,
      currentPage,
      () => sentenceItems.value[0]?.id ?? '',
      () => sentenceItems.value[0]?.start_offset ?? 0,
    ],
    () => {
      void loadLastSentenceItem()
    },
    { immediate: true },
  )

  return {
    activeProcessingId,
    sentenceItems,
    lastSentenceItem,
    lastSentenceLoading,
    currentPage,
    hasPreviousPage,
    hasNextPage,
    tableLoading,
    sentenceActionLoading,
    highlightedSentenceIds,
    showSegmentationLoading,
    tableRef,
    goToPreviousPage,
    goToNextPage,
    mergePreviousSentence,
    clipSentence,
  }
}
