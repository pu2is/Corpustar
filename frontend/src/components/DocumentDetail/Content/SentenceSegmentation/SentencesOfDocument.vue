<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
// components
import SymbolOfSentence from '@/components/DocumentDetail/Content/SentenceSegmentation/SymbolOfSentence.vue'
import WordOfSentence from '@/components/DocumentDetail/Content/SentenceSegmentation/WordOfSentence.vue'

// type
import type { SentenceItem } from '@/types/sentences'

const props = defineProps<{
  item: SentenceItem
  loading: boolean
  canMergePrev: boolean
  highlighted: boolean
  allowSentenceActions: boolean
}>()

const emit = defineEmits<{
  requestMerge: [sentenceId: string]
  clip: [sentenceId: string, splitOffset: number]
}>()

// Merge
function requestMergePrev(): void {
  emit('requestMerge', props.item.id)
}

// Clip
function requestClip(splitOffset: number | null): void {
  if (splitOffset === null) {
    return
  }
  emit('clip', props.item.id, splitOffset)
}

// Split sentence into words: punctuation first, then split by spaces.
interface SentenceWordToken {
  value: string
  isSymbol: boolean
  splitOffset: number | null
}

const wordTokens = computed(() => splitSentenceToWords(props.item.source_text, props.item.start_offset))
const sentenceContainerRef = ref<HTMLDivElement | null>(null)
const selectedSymbolWordIndex = ref<number | null>(null)
const selectedSymbolSplitOffset = computed(() => {
  if (selectedSymbolWordIndex.value === null) {
    return null
  }
  if (isLastWordToken(selectedSymbolWordIndex.value)) {
    return null
  }

  return wordTokens.value[selectedSymbolWordIndex.value]?.splitOffset ?? null
})
const canClip = computed(() => selectedSymbolSplitOffset.value !== null)

function requestClipByKeyboard(): void {
  if (props.loading || !canClip.value) {
    return
  }

  requestClip(selectedSymbolSplitOffset.value)
}

function isSymbolWord(word: string): boolean {
  const SYMBOL_WORD_PATTERN = /^[\p{P}\p{S}]+$/u
  return SYMBOL_WORD_PATTERN.test(word)
}

function isLastWordToken(wordIndex: number): boolean {
  return wordIndex === wordTokens.value.length - 1
}

function splitSentenceToWords(text: string, sentenceStartOffset: number): SentenceWordToken[] {
  const tokenPattern = /[\p{P}\p{S}]|[^\s\p{P}\p{S}]+/gu

  return Array.from(text.matchAll(tokenPattern), (match) => {
    const value = match[0]
    const isSymbol = isSymbolWord(value)

    return {
      value,
      isSymbol,
      splitOffset: isSymbol ? sentenceStartOffset + (match.index ?? 0) + 1 : null,
    }
  })
}

function toggleSymbolWord(wordIndex: number): void {
  const token = wordTokens.value[wordIndex]
  if (isLastWordToken(wordIndex) || !token?.isSymbol) return

  selectedSymbolWordIndex.value = selectedSymbolWordIndex.value === wordIndex ? null : wordIndex
  if (selectedSymbolWordIndex.value !== null) {
    void nextTick(() => {
      sentenceContainerRef.value?.focus()
    })
  }
}

watch(() => [props.item.id, props.item.source_text],
  () => {
    selectedSymbolWordIndex.value = null
  },
)
</script>

<template>
  <div ref="sentenceContainerRef"
    tabindex="0"
    class="border p-2 space-y-2 transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
    :class="highlighted ? 'border-emerald-500 bg-emerald-50/60' : 'border-border'"
    @keydown.enter.self.prevent="requestClipByKeyboard">
    <div class="min-w-0 flex-1 space-y-1">
      <!-- Header -->
      <p class="text-xs text-text-muted">
        {{ item.start_offset }} - {{ item.end_offset }}
      </p>
      <!-- Sentence text -->
      <div class="flex flex-wrap gap-1 break-words text-sm">
        <template v-for="(wordToken, wordIndex) in wordTokens"
          :key="`${item.id}-${wordIndex}`">
          <SymbolOfSentence v-if="wordToken.isSymbol"
            :value="wordToken.value" :is-last="isLastWordToken(wordIndex)"
            :selected="selectedSymbolWordIndex === wordIndex"
            @toggle="toggleSymbolWord(wordIndex)" />
          <WordOfSentence v-else
            :value="wordToken.value"
            :is-last="isLastWordToken(wordIndex)" />
        </template>
      </div>
    </div>
    <!-- Button area -->
    <div class="flex gap-2">
      <!-- Merge -->
      <button v-if="allowSentenceActions" type="button" :disabled="loading || !canMergePrev"
        class="rounded-sm px-3 py-0.5 text-xs bg-violet-200 text-violet-700 
          disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
        @click="requestMergePrev">
        Merge Prev
      </button>
      <!-- Clip -->
      <button v-if="allowSentenceActions" type="button" :disabled="loading || !canClip"
        class="rounded-sm px-3 py-0.5 text-xs bg-fuchsia-100 text-fuchsia-700 
          disabled:bg-gray-200 disabled:text-gray-600  disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
        @click="requestClip(selectedSymbolSplitOffset)">
        Clip
      </button>
    </div>
  </div>
</template>
