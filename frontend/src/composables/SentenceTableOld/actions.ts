import { nextTick, ref, type Ref } from 'vue'

import { usePaginationStore } from '@/stores/local/paginationStore'
import { useSentenceStore } from '@/stores/sentenceStore'
import type { SentenceItem } from '@/types/sentences'

import { useSentenceHighlight } from '@/composables/SentenceTableOld/highlightChange'

interface UseSentenceActionsOptions {
  sentenceItems: Ref<SentenceItem[]>
  lastSentenceItem: Ref<SentenceItem | null>
  scrollAreaRef: Ref<HTMLDivElement | null>
  lastSentenceOnPrevPage: Map<string, SentenceItem | null>
}

function getPreviousSentenceId(
  sentenceId: string,
  sentenceItems: SentenceItem[],
  lastSentenceItem: SentenceItem | null,
): string | null {
  const sentenceIndex = sentenceItems.findIndex((item) => item.id === sentenceId)

  if (sentenceIndex < 0) {
    return null
  }

  if (sentenceIndex > 0) {
    return sentenceItems[sentenceIndex - 1]?.id ?? null
  }

  return sentenceItems[0]?.start_offset === 0 ? null : lastSentenceItem?.id ?? null
}

function getClippedSentenceIdsOnCurrentPage(
  sentenceItems: SentenceItem[],
  originalSentence: SentenceItem | null,
  splitOffset: number,
): string[] {
  if (originalSentence === null) {
    return []
  }

  const leftSentenceId = sentenceItems.find((item) => (
    item.start_offset === originalSentence.start_offset
    && item.end_offset === splitOffset
  ))?.id ?? ''
  const rightSentenceId = sentenceItems.find((item) => (
    item.start_offset === splitOffset
    && item.end_offset === originalSentence.end_offset
  ))?.id ?? ''

  return Array.from(new Set([leftSentenceId, rightSentenceId].filter(Boolean)))
}

export function useSentenceActions(options: UseSentenceActionsOptions) {
  const paginationStore = usePaginationStore()
  const sentenceStore = useSentenceStore()
  const { highlightedSentenceIdSet, applyHighlightChange } = useSentenceHighlight()

  const mutationLoading = ref(false)
  const pendingScrollTop = ref<number | null>(null)

  function captureScrollPosition(): void {
    const scrollArea = options.scrollAreaRef.value
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
    if (options.scrollAreaRef.value) {
      options.scrollAreaRef.value.scrollTop = scrollTop
    }
  }

  function resetActionState(): void {
    pendingScrollTop.value = null
  }

  async function mergePreviousSentence(sentenceId: string): Promise<void> {
    const currentSentence = options.sentenceItems.value.find((item) => item.id === sentenceId) ?? null
    const docId = currentSentence?.doc_id ?? ''
    const segmentationId = currentSentence?.version_id ?? ''
    const previousSentenceId = getPreviousSentenceId(
      sentenceId,
      options.sentenceItems.value,
      options.lastSentenceItem.value,
    )
    if (!previousSentenceId || !docId || !segmentationId) {
      return
    }

    captureScrollPosition()
    mutationLoading.value = true
    try {
      const mergedItem = await sentenceStore.mergeSentences([previousSentenceId, sentenceId])
      applyHighlightChange({ type: 'merge', mergedSentenceId: mergedItem.id })
      options.lastSentenceOnPrevPage.clear()
      await paginationStore.refreshCurrentPage(docId, segmentationId, 'sentence')
      await restoreScrollPosition()
    } catch {
      pendingScrollTop.value = null
    } finally {
      mutationLoading.value = false
    }
  }

  async function clipSentence(sentenceId: string, splitOffset: number): Promise<void> {
    const originalSentence = options.sentenceItems.value.find((item) => item.id === sentenceId) ?? null
    const docId = originalSentence?.doc_id ?? ''
    const segmentationId = originalSentence?.version_id ?? ''
    if (!docId || !segmentationId) {
      return
    }

    captureScrollPosition()
    mutationLoading.value = true
    try {
      await sentenceStore.clipSentence(sentenceId, splitOffset)
      options.lastSentenceOnPrevPage.clear()
      await paginationStore.refreshCurrentPage(docId, segmentationId, 'sentence')
      applyHighlightChange({
        type: 'clip',
        clippedSentenceIds: getClippedSentenceIdsOnCurrentPage(
          options.sentenceItems.value,
          originalSentence,
          splitOffset,
        ),
      })
      await restoreScrollPosition()
    } catch {
      pendingScrollTop.value = null
    } finally {
      mutationLoading.value = false
    }
  }

  return {
    highlightedSentenceIdSet,
    mutationLoading,
    mergePreviousSentence,
    clipSentence,
    resetActionState,
  }
}
