import { computed, type Ref } from 'vue'
import type { SentenceItem } from '@/types/sentences'

export interface SentenceWordToken {
  key: string
  value: string
  isSymbol: boolean
  splitOffset: number | null
}

const TOKEN_PATTERN = /[\p{P}\p{S}]|[^\s\p{P}\p{S}]+/gu
const SYMBOL_WORD_PATTERN = /^[\p{P}\p{S}]+$/u

export function splitSentenceToWords(item: SentenceItem): SentenceWordToken[] {
  return Array.from(item.source_text.matchAll(TOKEN_PATTERN), (match, index) => {
    const value = match[0]
    const isSymbol = SYMBOL_WORD_PATTERN.test(value)

    return {
      key: `${item.id}-${index}`,
      value,
      isSymbol,
      splitOffset: isSymbol ? item.start_offset + (match.index ?? 0) + 1 : null,
    }
  })
}

export function useSentenceTokenById(sentenceItems: Ref<SentenceItem[]>) {
  const sentenceTokensById = computed(() => new Map<string, SentenceWordToken[]>(
    sentenceItems.value.map((item) => [item.id, splitSentenceToWords(item)]),
  ))

  return {
    sentenceTokensById,
  }
}
