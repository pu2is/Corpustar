<script setup lang="ts">
import { computed, ref } from 'vue'
import { useSentenceStore } from '@/stores/sentenceStore'

const sentenceStore = useSentenceStore()
const sentenceList = computed(() => sentenceStore.sentenceList);
const highlightedSentenceIdSet = computed(() => new Set(sentenceStore.sentenceList.highlight))

interface TokenItem {
  text: string
  isSymbol: boolean
}

interface SentenceStoreMergeAction {
  mergeSentence?: (sentenceIds: string[]) => Promise<unknown>
}

const edit = ref<boolean>(false);

// Tokens: merge & split
const tokens = computed(() => new Map(
  sentenceList.value.sentences.map((item) => [item.id, sentenceToTokens(item.source_text)]),
))

function sentenceToTokens(sentence: string): TokenItem[] {
  if (sentence.length === 0) { return [] }
  const TOKEN_PATTERN = /([\p{P}\p{S}])|([^\s\p{P}\p{S}]+)/gu

  return Array.from(sentence.matchAll(TOKEN_PATTERN), (match) => ({
    text: match[0],
    isSymbol: match[1] !== undefined,
  }))
}

function isLastToken(tokens: TokenItem[], tokenIndex: number): boolean {
  return tokenIndex === tokens.length - 1
}

function canMergePrevious(index: number): boolean {
  if (index > 0) { return true}
  return sentenceList.value.prevSentence !== null
}

async function requestMerge(index: number, sentenceId: string): Promise<void> {
  const previousSentenceId = index > 0
    ? (sentenceList.value.sentences[index - 1]?.id ?? null)
    : (sentenceList.value.prevSentence?.id ?? null)
  if (!previousSentenceId) {
    return
  }

  const mergeSentence = (sentenceStore as unknown as SentenceStoreMergeAction).mergeSentence
  if (typeof mergeSentence === 'function') {
    await mergeSentence([previousSentenceId, sentenceId])
    return
  }

  await sentenceStore.mergeSentences([previousSentenceId, sentenceId])
}

</script>

<template>
  <article v-for="(item, index) in sentenceList.sentences"
    :key="item.id"
    class="mb-2 border p-2 transition-colors duration-200"
    :class="highlightedSentenceIdSet.has(item.id) ? 'border-emerald-500 bg-emerald-50/60' : 'border-border'">
    <p class="text-xs text-text-muted">
      {{ item.start_offset }} - {{ item.end_offset }}
    </p>

    <!-- Merge & Clip UI -->
    <div v-if="!edit"
      class="mt-1 flex flex-wrap gap-1 break-words text-sm">
      <template v-for="(token, tokenIndex) in tokens.get(item.id) ?? []"
        :key="`${item.id}-${tokenIndex}`">

        <button v-if="token.isSymbol" type="button"
          class="rounded-none px-1 transition-colors duration-150"
          :class="isLastToken(tokens.get(item.id) ?? [], tokenIndex)
            ? ''
            : 'cursor-pointer hover:bg-emerald-600 hover:text-emerald-50'">
          {{ token.text }}
        </button>
        <span v-else
          class="rounded-none px-1 transition-colors duration-150"
          :class="isLastToken(tokens.get(item.id) ?? [], tokenIndex)
            ? '' : 'cursor-default hover:bg-sky-600 hover:text-sky-100'">
          {{ token.text }}
        </span>
      </template>
    </div>

    <!-- Edit UI -->
    <input v-else
      :value="item.corrected_text || item.source_text"
      class="mt-1 w-full border border-border px-2 py-1 text-sm"
      @input="item.corrected_text = ($event.target as HTMLInputElement).value">

    <!-- Actions -->
    <div class="mt-2 flex gap-2">
      <button type="button"
        :disabled="!canMergePrevious(index)"
        class="cursor-pointer bg-violet-200 px-3 py-0.5 text-xs text-violet-700 disabled:cursor-not-allowed disabled:opacity-60"
        @click="void requestMerge(index, item.id)">
        Merge Prev
      </button>
      <button type="button"
        class="cursor-pointer bg-fuchsia-100 px-3 py-0.5 text-xs text-fuchsia-700">
        Clip
      </button>
    </div>
  </article>
</template>
