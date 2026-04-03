import type { ComputedRef } from 'vue'

import { useSentenceStore } from '@/stores/sentenceStore'
import type { SentenceListItem } from '@/types/sentences'

interface ComputedSentenceListItem {
  sentenceList: ComputedRef<SentenceListItem>
}

function getPreviousSentenceId(sentenceList: SentenceListItem, index: number): string | null {
  if (index > 0) {
    return sentenceList.sentences[index - 1]?.id ?? null
  }

  return sentenceList.prevSentence?.id ?? null
}

export function mergePrevSentence(sentenceListItem: ComputedSentenceListItem) {
  const sentenceStore = useSentenceStore()

  const merge = {
    canPrevious(index: number): boolean {
      return getPreviousSentenceId(sentenceListItem.sentenceList.value, index) !== null
    },
    async previous(index: number, sentenceId: string): Promise<void> {
      const previousSentenceId = getPreviousSentenceId(sentenceListItem.sentenceList.value, index)
      if (!previousSentenceId) {
        return
      }

      await sentenceStore.mergeSentences([previousSentenceId, sentenceId])
    },
  }

  return {
    merge,
  }
}
