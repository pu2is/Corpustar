import { ref, type ComputedRef, type Ref } from 'vue'

import { useSentenceStore } from '@/stores/sentenceStore'
import type { SentenceListItem } from '@/types/sentences'

interface ComputedSentenceListItem {
  sentenceList: ComputedRef<SentenceListItem>
}

interface ClipToken {
  isSymbol: boolean
  splitOffset: number
}

interface ClipCandidate {
  sentenceId: string
  splitOffset: number
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

export class ClipSentenceAction {
  private readonly sentenceStore = useSentenceStore()
  readonly selectedClip: Ref<ClipCandidate | null> = ref(null)

  clear(): void {
    this.selectedClip.value = null
  }

  isSelected(sentenceId: string, splitOffset: number): boolean {
    return this.selectedClip.value?.sentenceId === sentenceId
      && this.selectedClip.value.splitOffset === splitOffset
  }

  toggle(sentenceId: string, token: ClipToken): void {
    if (!token.isSymbol) {
      return
    }

    if (this.isSelected(sentenceId, token.splitOffset)) {
      this.clear()
      return
    }

    this.selectedClip.value = { sentenceId, splitOffset: token.splitOffset }
  }

  canClip(sentenceId: string): boolean {
    return this.selectedClip.value?.sentenceId === sentenceId
  }

  async clip(sentenceId: string): Promise<void> {
    if (!this.canClip(sentenceId) || this.selectedClip.value === null) {
      return
    }

    const splitOffset = this.selectedClip.value.splitOffset
    this.clear()
    await this.sentenceStore.clipSentence(sentenceId, splitOffset)
  }
}
