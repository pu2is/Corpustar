import { computed, watch, type Ref } from 'vue'
import { useLemmaStore } from '@/stores/lemmaStore'
import { usePaginationStore } from '@/stores/local/paginationStore'
import { useProcessStore } from '@/stores/processStore'
import type { LemmaViewItem } from '@/types/lemmatize'

export function useLemmatizationTable(docId: Ref<string>) {
  const lemmaStore = useLemmaStore()
  const paginationStore = usePaginationStore()
  const processStore = useProcessStore()

  const processItemsByDocId = computed(() => processStore.getProcessesByDocId(docId.value))
  const activeSegmentation = computed(() => processStore.getSentenceSegmentationProcessByDocId(docId.value))
  const activeSegmentationId = computed(() => activeSegmentation.value?.id ?? '')
  const activeLemmatizeProcess = computed(() => processStore.getLemmatizeProcessBySegmentationId(
    docId.value,
    activeSegmentationId.value,
  ))
  const hasLemmatizeProcess = computed(() => (
    processItemsByDocId.value.some((process) => process.type === 'lemma')
  ))
  const activeDocProcessKey = computed(() => (
    docId.value && activeSegmentationId.value ? `${docId.value}::${activeSegmentationId.value}` : ''
  ))

  const paginationEntry = computed(() => paginationStore.getPaginationEntry(docId.value, 'lemma'))
  const paginationReady = computed(() => paginationEntry.value.processingId === activeSegmentationId.value)
  const pageLoading = computed(() => paginationEntry.value.loading)
  const currentPage = computed(() => paginationEntry.value.currentPage)
  const hasPreviousPage = computed(() => currentPage.value > 1)
  const hasNextPage = computed(() => paginationEntry.value.hasMore)
  const lemmaItemIds = computed(() => paginationEntry.value.pageItemIds)
  const storedLemmaMap = computed(() => new Map<string, LemmaViewItem>(
    lemmaStore
      .getLemmasBySegmentationId(activeSegmentationId.value)
      .map((item) => [item.id, item]),
  ))
  const lemmaItems = computed(() => lemmaItemIds.value
    .map((itemId) => storedLemmaMap.value.get(itemId))
    .filter((item): item is LemmaViewItem => item !== undefined),
  )
  const showLemmaLoading = computed(() => (
    activeLemmatizeProcess.value?.state === 'running'
    || (Boolean(activeSegmentationId.value) && hasLemmatizeProcess.value
      && (!paginationReady.value || (pageLoading.value && lemmaItems.value.length === 0)))
  ))

  async function goToPreviousPage(): Promise<void> {
    const currentDocId = docId.value
    const processingId = activeSegmentationId.value
    if (!currentDocId || !processingId || !hasPreviousPage.value || pageLoading.value) {
      return
    }

    await paginationStore.goToPreviousPage(currentDocId, processingId, 'lemma')
  }

  async function goToNextPage(): Promise<void> {
    const currentDocId = docId.value
    const processingId = activeSegmentationId.value
    if (!currentDocId || !processingId || !hasNextPage.value || pageLoading.value) {
      return
    }

    await paginationStore.goToNextPage(currentDocId, processingId, 'lemma')
  }

  watch(
    activeDocProcessKey,
    async (nextKey) => {
      if (!nextKey || !docId.value || !activeSegmentationId.value || !hasLemmatizeProcess.value) {
        return
      }

      await paginationStore.initializeDocumentPagination(docId.value, activeSegmentationId.value, 'lemma')
    },
    { immediate: true },
  )

  watch(
    () => activeLemmatizeProcess.value?.state ?? '',
    (state) => {
      if (state !== 'succeed' || !docId.value || !activeSegmentationId.value) {
        return
      }

      void paginationStore.refreshCurrentPage(docId.value, activeSegmentationId.value, 'lemma')
    },
  )

  watch(
    [
      activeDocProcessKey,
      () => lemmaItemIds.value.join('|'),
      () => lemmaStore.getLemmasBySegmentationId(activeSegmentationId.value).map((item) => item.id).join('|'),
    ],
    ([nextKey, pageItemIds, storedLemmaIds]) => {
      if (!nextKey || !docId.value || !activeSegmentationId.value || pageItemIds || !storedLemmaIds) {
        return
      }

      void paginationStore.refreshCurrentPage(docId.value, activeSegmentationId.value, 'lemma')
    },
    { immediate: true },
  )

  return {
    hasLemmatizeProcess,
    lemmaItems,
    currentPage,
    hasPreviousPage,
    hasNextPage,
    pageLoading,
    showLemmaLoading,
    goToPreviousPage,
    goToNextPage,
  }
}
