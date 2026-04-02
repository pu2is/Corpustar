import { computed, ref } from 'vue'

export type SentenceHighlightChangeEvent =
  | { type: 'clip'; clippedSentenceIds: string[] }
  | { type: 'merge'; mergedSentenceId: string }
  | { type: 'corrected'; correctedSentenceId: string }

export function useSentenceHighlight() {
  const highlightedSentenceIds = ref<string[]>([])

  const highlightedSentenceIdSet = computed(
    () => new Set(highlightedSentenceIds.value),
  )

  function setHighlightedSentenceIds(sentenceIds: string[]): void {
    highlightedSentenceIds.value = Array.from(new Set(sentenceIds.filter(Boolean)))
  }

  function clearHighlightedSentenceIds(): void {
    setHighlightedSentenceIds([])
  }

  function applyHighlightChange(event: SentenceHighlightChangeEvent): void {
    if (event.type === 'merge') {
      setHighlightedSentenceIds([event.mergedSentenceId])
      return
    }

    if (event.type === 'clip') {
      setHighlightedSentenceIds(event.clippedSentenceIds)
      return
    }

    if (event.type === 'corrected') {
      setHighlightedSentenceIds([event.correctedSentenceId])
      return
    }

    clearHighlightedSentenceIds()
  }

  return {
    highlightedSentenceIdSet,
    applyHighlightChange,
  }
}
