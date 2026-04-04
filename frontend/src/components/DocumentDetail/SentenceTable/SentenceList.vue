<script setup lang="ts">
import { computed, ref } from 'vue'
import { Pencil, RefreshCw, Save } from 'lucide-vue-next'
import { ClipSentenceAction, mergePrevSentence } from '@/composables/SentenceTable/actions'
import { useSentenceStore } from '@/stores/sentenceStore'
import type { SentenceItem } from '@/types/sentences'

const sentenceStore = useSentenceStore()
const sentenceList = computed(() => sentenceStore.sentenceList);
const highlightedSentenceIdSet = computed(() => new Set(sentenceStore.sentenceList.highlight))

// Tokens
interface TokenItem {
  text: string
  isSymbol: boolean
  splitOffset: number
}

const tokens = computed(() => new Map(
  sentenceList.value.sentences.map((item) => [
    item.id,
    sentenceToTokens(item.corrected_text || item.source_text, item.start_offset),
  ]),
))

function sentenceToTokens(sentence: string, sentenceStartOffset: number): TokenItem[] {
  if (sentence.length === 0) { return [] }
  const tokenPattern = /[\p{P}\p{S}]|[^\s\p{P}\p{S}]+/gu

  return Array.from(sentence.matchAll(tokenPattern), (match) => {
    const text = match[0]
    const isSymbol = /^[\p{P}\p{S}]+$/u.test(text)

    return {
      text,
      isSymbol,
      splitOffset: sentenceStartOffset + (match.index ?? 0) + 1,
    }
  })
}

function isLastToken(tokens: TokenItem[], tokenIndex: number): boolean {
  return tokenIndex === tokens.length - 1
}

// Edit: Merge & Clip availability
function allowMergeAndCip(sentenceItem: SentenceItem): boolean {
  return sentenceItem.source_text.trim() === sentenceItem.corrected_text.trim()
}

function getPrevSentence(index: number): SentenceItem | null {
  return index > 0
    ? (sentenceList.value.sentences[index - 1] ?? null)
    : sentenceList.value.prevSentence
}

function canMergePrev(index: number, item: SentenceItem): boolean {
  const prevSentence = getPrevSentence(index)
  if (!prevSentence) {
    return false
  }

  return allowMergeAndCip(item) && allowMergeAndCip(prevSentence)
}

// Edit
const correctedText = ref<string>('')

function startEdit(item: SentenceItem): void {
  clipAction.clear()
  focusOn.value = item.id
  correctedText.value = item.corrected_text
}

async function resetToSource(item: SentenceItem): Promise<void> {
  await sentenceStore.correctSentence(item.id, item.source_text)
  focusOn.value = ''
}


async function saveEdit(sentenceId: string): Promise<void> {
  if (!isEdit(sentenceId)) { return}

  await sentenceStore.correctSentence(sentenceId, correctedText.value)
  focusOn.value = ''
}

// Clip: choose split token.
function handleTokenClick(item: SentenceItem, token: TokenItem, event: MouseEvent): void {
  if (!allowMergeAndCip(item)) {
    return
  }

  const sentenceId = item.id
  if (focusOn.value && focusOn.value !== sentenceId) {
    clipAction.clear()
  }

  clipAction.toggle(sentenceId, token)
  if (clipAction.canClip(sentenceId)) {
    focusOn.value = sentenceId
    const article = (event.currentTarget as HTMLElement | null)?.closest('article')
    article?.focus()
    return
  }

  if (focusOn.value === sentenceId) { focusOn.value = '' }
}

// focus: one sentence. edit mode or clip mode.
const focusOn = ref<string>('')

function isEdit(sentenceId: string): boolean {
  return focusOn.value === sentenceId && !clipAction.canClip(sentenceId)
}

// actions
const { merge } = mergePrevSentence({ sentenceList })
async function handleMergePrev(index: number, item: SentenceItem): Promise<void> {
  if (!canMergePrev(index, item)) { return }
  await merge.previous(index, item.id)
}

const clipAction = new ClipSentenceAction()
async function handlieClip(item: SentenceItem): Promise<void> {
  if (!allowMergeAndCip(item)) {
    return
  }

  const sentenceId = item.id
  if (!clipAction.canClip(sentenceId)) {
    return
  }

  await clipAction.clip(sentenceId)
  if (focusOn.value === sentenceId) { focusOn.value = ''}
}
</script>

<template>
  <article v-for="(item, index) in sentenceList.sentences"
    :key="item.id"
    tabindex="0"
    class="mb-2 border p-2 transition-colors duration-200"
    :class="highlightedSentenceIdSet.has(item.id) ? 'border-emerald-500 bg-emerald-50/60' : 'border-border'"
    @keydown.enter.self.prevent="void handlieClip(item)">
    <!-- {{ item.corrected_text === item.source_text }} {{ item.corrected_text }} {{ item.source_text }} -->
    <div class="flex items-center justify-between">
      <p class="text-xs text-text-muted">
        {{ item.start_offset }} - {{ item.end_offset }}
      </p>
      <div class="flex items-center gap-1">
        
        <button v-if="isEdit(item.id)"
          type="button"
          class="cursor-pointer rounded p-1 text-text-muted transition-colors hover:bg-border hover:text-text-default"
          @click="void saveEdit(item.id)">
          <Save class="h-4 w-4" />
        </button>

        <template v-else>
          <button v-if="!allowMergeAndCip(item)"
            type="button"
            class="cursor-pointer rounded p-1 text-text-muted transition-colors hover:bg-border hover:text-text-default"
            @click="void resetToSource(item)">
            <RefreshCw class="h-4 w-4" />
          </button>
          <button type="button"
            class="cursor-pointer rounded p-1 text-text-muted transition-colors hover:bg-border hover:text-text-default"
            @click="startEdit(item)">
            <Pencil class="h-4 w-4" />
          </button>
        </template>
      </div>
    </div>

    <!-- Merge & Clip UI -->
    <div v-if="!isEdit(item.id)"
      class="mt-1 flex flex-wrap gap-1 break-words text-sm">
      <template v-for="(token, tokenIndex) in tokens.get(item.id) ?? []"
        :key="`${item.id}-${tokenIndex}`">

        <button v-if="token.isSymbol" type="button"
          class="rounded-none px-1 transition-colors duration-150"
          :class="[
            'cursor-pointer hover:bg-emerald-600 hover:text-emerald-50',
            clipAction.isSelected(item.id, token.splitOffset) ? 'bg-emerald-700 text-emerald-50' : '',
          ]"
          @click="handleTokenClick(item, token, $event)">
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
      :value="correctedText"
      class="mt-1 w-full border-0 rounded-none bg-white px-2 py-1 text-sm focus:outline-none focus:ring-0"
      @input="correctedText = ($event.target as HTMLInputElement).value"
      @keydown.enter.prevent="void saveEdit(item.id)">

    <!-- Actions -->
    <div class="mt-2 flex gap-2">
      <button type="button"
        :disabled="!canMergePrev(index, item)"
        class="cursor-pointer bg-violet-200 px-3 py-0.5 text-xs text-violet-700 disabled:cursor-not-allowed disabled:opacity-60"
        @click="void handleMergePrev(index, item)">
        Merge Prev
      </button>
      <button type="button"
        :disabled="!clipAction.canClip(item.id) || !allowMergeAndCip(item)"
        class="cursor-pointer bg-fuchsia-100 px-3 py-0.5 text-xs text-fuchsia-700 disabled:cursor-not-allowed disabled:bg-gray-200 disabled:text-gray-600 disabled:opacity-60"
        @click="void handlieClip(item)">
        Clip
      </button>
    </div>    
  </article>
</template>
