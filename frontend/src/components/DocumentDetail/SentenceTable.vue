<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useSentenceSegmentationTable, type SegmentItem } from '@/composables/documentDetail/useSentenceSegmentationTable'
import type { SentenceItem } from '@/types/sentences'

const props = defineProps<{
  docId: string
}>()

interface SentenceWordToken {
  key: string
  value: string
  isSymbol: boolean
  splitOffset: number | null
}

const segmentItem: SegmentItem = useSentenceSegmentationTable(computed(() => props.docId))

const scrollAreaRef = ref<HTMLDivElement | null>(null)
const selectedClip = ref<{ sentenceId: string; splitOffset: number } | null>(null)
const highlightedSentenceIdSet = computed(() => new Set(segmentItem.highlightedSentenceIds.value))
const sentenceTokensById = computed(() => new Map<string, SentenceWordToken[]>(
  segmentItem.sentenceItems.value.map((item) => [item.id, splitSentenceToWords(item)]),
))

function getScrollAreaElement(): HTMLDivElement | null {
  return scrollAreaRef.value
}

segmentItem.tableRef.value = { getScrollAreaElement }

function splitSentenceToWords(item: SentenceItem): SentenceWordToken[] {
  const tokenPattern = /[\p{P}\p{S}]|[^\s\p{P}\p{S}]+/gu
  return Array.from(item.source_text.matchAll(tokenPattern), (match, index) => {
    const value = match[0]
    const isSymbol = /^[\p{P}\p{S}]+$/u.test(value)
    return {
      key: `${item.id}-${index}`,
      value,
      isSymbol,
      splitOffset: isSymbol ? item.start_offset + (match.index ?? 0) + 1 : null,
    }
  })
}

function isLastToken(sentenceId: string, tokenIndex: number): boolean {
  const sentenceTokens = sentenceTokensById.value.get(sentenceId) ?? []
  return tokenIndex === sentenceTokens.length - 1
}

function canMergePrevious(index: number, item: SentenceItem): boolean {
  return index > 0 || (index === 0 && item.start_offset > 0 && segmentItem.lastSentenceItem.value !== null)
}

function isSelectedSplit(sentenceId: string, splitOffset: number | null): boolean {
  if (splitOffset === null || selectedClip.value === null) {
    return false
  }
  return selectedClip.value.sentenceId === sentenceId && selectedClip.value.splitOffset === splitOffset
}

function toggleSplit(sentenceId: string, splitOffset: number | null, isLast: boolean): void {
  if (splitOffset === null || isLast || segmentItem.tableLoading.value) {
    return
  }
  if (isSelectedSplit(sentenceId, splitOffset)) {
    selectedClip.value = null
    return
  }

  selectedClip.value = { sentenceId, splitOffset }
}

function canClip(sentenceId: string): boolean {
  return selectedClip.value?.sentenceId === sentenceId
}

async function requestMerge(sentenceId: string): Promise<void> {
  selectedClip.value = null
  await segmentItem.mergePreviousSentence(sentenceId)
}

async function requestClip(sentenceId: string): Promise<void> {
  const splitOffset = selectedClip.value?.sentenceId === sentenceId
    ? selectedClip.value.splitOffset
    : null
  if (splitOffset === null || segmentItem.tableLoading.value) {
    return
  }

  selectedClip.value = null
  await segmentItem.clipSentence(sentenceId, splitOffset)
}

watch([segmentItem.activeProcessingId, segmentItem.currentPage], () => {
  selectedClip.value = null
})

watch(segmentItem.sentenceItems, (items) => {
  if (selectedClip.value === null) {
    return
  }
  if (!items.some((item) => item.id === selectedClip.value?.sentenceId)) {
    selectedClip.value = null
  }
})
</script>

<template>
  <section class="min-h-0 flex flex-1 flex-col overflow-hidden bg-background-elevated/15">
    <p v-if="segmentItem.showSegmentationLoading.value"
      class="p-3 text-sm text-text-muted">
      Loading sentences...
    </p>
    <p v-else-if="segmentItem.sentenceItems.value.length === 0"
      class="p-3 text-sm text-text-muted">
      No sentences in this segmentation result.
    </p>

    <template v-else>
      <div ref="scrollAreaRef"
        class="scroll-area min-h-0 flex-1 overflow-y-auto">
        <article v-if="segmentItem.lastSentenceItem.value"
          class="sticky top-0 z-10 mb-2 bg-violet-200/60 px-4 py-3 text-violet-950 backdrop-blur-md">
          <div class="flex items-start justify-between gap-3">
            <div class="space-y-1">
              <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-violet-800/80">
                Previous Sentence
              </p>
              <p class="text-xs text-violet-900/80">
                {{ segmentItem.lastSentenceItem.value.start_offset }} - {{ segmentItem.lastSentenceItem.value.end_offset }}
              </p>
              <p class="line-clamp-2 break-words text-sm font-medium text-violet-950">
                {{ segmentItem.lastSentenceItem.value.source_text }}
              </p>
            </div>
            <span
              v-if="segmentItem.sentenceActionLoading.value || segmentItem.lastSentenceLoading.value"
              class="shrink-0 rounded bg-white/40 px-2 py-1 text-[11px] font-semibold text-violet-900/75">
              Updating
            </span>
          </div>
        </article>

        <article v-for="(item, index) in segmentItem.sentenceItems.value"
          :key="item.id"
          class="mb-2 border p-2 transition-colors duration-200"
          :class="highlightedSentenceIdSet.has(item.id) ? 'border-emerald-500 bg-emerald-50/60' : 'border-border'">
          <p class="text-xs text-text-muted">
            {{ item.start_offset }} - {{ item.end_offset }}
          </p>

          <div class="mt-1 flex flex-wrap gap-1 break-words text-sm">
            <template v-for="(wordToken, wordIndex) in sentenceTokensById.get(item.id) ?? []"
              :key="wordToken.key">
              <button v-if="wordToken.isSymbol"
                type="button"
                :disabled="isLastToken(item.id, wordIndex) || segmentItem.tableLoading.value"
                class="rounded-none px-1 transition-colors duration-150 disabled:cursor-default"
                :class="[
                  isLastToken(item.id, wordIndex)
                    ? ''
                    : 'cursor-pointer hover:bg-emerald-600 hover:text-emerald-50',
                  isSelectedSplit(item.id, wordToken.splitOffset) ? 'bg-emerald-700 text-emerald-50' : '',
                ]"
                @click="toggleSplit(item.id, wordToken.splitOffset, isLastToken(item.id, wordIndex))">
                {{ wordToken.value }}
              </button>
              <span
                v-else
                class="rounded-none px-1 transition-colors duration-150"
                :class="isLastToken(item.id, wordIndex) ? '' : 'hover:bg-sky-600 hover:text-sky-100'">
                {{ wordToken.value }}
              </span>
            </template>
          </div>

          <div class="mt-2 flex gap-2">
            <button type="button"
              :disabled="segmentItem.sentenceActionLoading.value || !canMergePrevious(index, item)"
              class="cursor-pointer bg-violet-200 px-3 py-0.5 text-xs text-violet-700 disabled:cursor-not-allowed disabled:opacity-60"
              @click="void requestMerge(item.id)">
              Merge Prev
            </button>
            <button type="button"
              :disabled="segmentItem.sentenceActionLoading.value || !canClip(item.id)"
              class="cursor-pointer bg-fuchsia-100 px-3 py-0.5 text-xs text-fuchsia-700 disabled:cursor-not-allowed disabled:bg-gray-200 disabled:text-gray-600 disabled:opacity-60"
              @click="void requestClip(item.id)">
              Clip
            </button>
          </div>
        </article>
      </div>

      <footer class="bg-violet-200/60 px-4 py-3 text-violet-950 shadow-[0_16px_36px_-24px_rgba(109,40,217,0.9)] backdrop-blur-md">
        <div class="flex items-center justify-between gap-3">
          <p class="text-sm font-medium">
            Page {{ segmentItem.currentPage.value }}
          </p>
          <div class="flex items-center gap-2">
            <button
              type="button"
              :disabled="segmentItem.tableLoading.value || !segmentItem.hasPreviousPage.value"
              class="cursor-pointer bg-white/45 px-3 py-1.5 text-xs font-semibold text-violet-900 transition hover:bg-white/70 disabled:cursor-not-allowed disabled:opacity-45"
              @click="void segmentItem.goToPreviousPage()">
              Prev
            </button>
            <button
              type="button"
              :disabled="segmentItem.tableLoading.value || !segmentItem.hasNextPage.value"
              class="cursor-pointer bg-violet-500 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-violet-600/85 disabled:cursor-not-allowed disabled:opacity-45"
              @click="void segmentItem.goToNextPage()">
              Next
            </button>
          </div>
        </div>
      </footer>
    </template>
  </section>
</template>
