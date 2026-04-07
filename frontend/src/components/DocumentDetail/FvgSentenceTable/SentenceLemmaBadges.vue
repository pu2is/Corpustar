<script setup lang="ts">
import { ref, watch } from 'vue'
import { Pin, X, CirclePlus, CircleCheck } from 'lucide-vue-next'
import { CollapsibleRoot, CollapsibleTrigger, CollapsibleContent } from 'reka-ui'
import type { LemmaItem } from '@/types/lemmatize'

const props = defineProps<{
  lemmaTokens: LemmaItem[]
  isActive: boolean
  clearSignal?: number
}>()

const emit = defineEmits<{
  hoverLemma: [wordIndex: number | null]
  pinned: []
  chosenIndices: [wordIndices: number[]]
}>()

const hoverId = ref<string | null>(null)

// Lemma info details panel
watch(() => props.isActive, (active) => {
  if (!active) pinnedOrder.value = []
})

watch(() => props.clearSignal, () => {
  chosenIds.value = new Set()
})

function isPinned(id: string): boolean {
  return pinnedOrder.value.includes(id)
}

function isDetailOpen(id: string): boolean {
  return hoverId.value === id || isPinned(id)
}

function togglePin(id: string): void {
  if (isPinned(id)) {
    pinnedOrder.value = pinnedOrder.value.filter((i) => i !== id)
  } else {
    pinnedOrder.value = [...pinnedOrder.value, id]
    emit('pinned')
  }
}

function bringToFront(id: string): void {
  if (!isPinned(id)) return
  pinnedOrder.value = [...pinnedOrder.value.filter((i) => i !== id), id]
}

const pinnedOrder = ref<string[]>([])

function panelZIndex(id: string): number {
  if (hoverId.value === id && !isPinned(id)) return 20
  const idx = pinnedOrder.value.indexOf(id)
  return idx !== -1 ? 10 + idx : 10
}

// Choose lemma tokens
const chosenIds = ref<Set<string>>(new Set())

function isChosen(id: string): boolean {
  return chosenIds.value.has(id)
}

function toggleChosen(id: string): void {
  const next = new Set(chosenIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  chosenIds.value = next
  const wordIndices = props.lemmaTokens
    .filter((l) => next.has(l.id))
    .map((l) => l.word_index)
  emit('chosenIndices', wordIndices)
}
</script>

<template>
  <div class="flex flex-wrap gap-1 text-xs text-text-muted">
    <CollapsibleRoot v-for="lemma in lemmaTokens"
      :key="lemma.id"
      :open="isDetailOpen(lemma.id)"
      class="relative"
      @mouseenter="hoverId = lemma.id; emit('hoverLemma', lemma.word_index)"
      @mouseleave="hoverId = null; emit('hoverLemma', null)">
      <span :class="[
          'cursor-pointer inline-flex items-center gap-0.5 px-1 py-0.5',
          lemma.pos_tag === 'ADP' ? 'bg-background-elevated text-violet-700' :
          lemma.pos_tag === 'VERB' ? 'bg-amber-50 text-amber-700' :
          lemma.pos_tag === 'NOUN'  ? 'bg-blue-50 text-blue-600' :
          ['PRON', 'PROPN', 'DET', 'PUNCT', 'SPACE', 'SYM', 'X', 'ADV'].includes(lemma.pos_tag)
            ? 'bg-background-elevated text-gray-300' :
          'bg-background-elevated text-gray-500'
        ]"
        @click="toggleChosen(lemma.id)">
        <span class="flex-shrink-0 transition-colors"
          :class="isChosen(lemma.id) ? 'text-green-500' : 'text-gray-300'">
          <CircleCheck v-if="isChosen(lemma.id)" :size="9" />
          <CirclePlus v-else :size="9" />
        </span>
        <span :class="isChosen(lemma.id) ? 'font-bold' : ''">{{ lemma.lemma_word }}</span>
        <CollapsibleTrigger as-child>
          <button :class="['cursor-pointer transition-colors', isPinned(lemma.id) ? 'text-yellow-500' : 'text-gray-300 hover:text-gray-500']"
            @click.stop="togglePin(lemma.id)">
            <Pin :size="8" fill="currentColor" />
          </button>
        </CollapsibleTrigger>
      </span>

      <CollapsibleContent
        :style="{ zIndex: panelZIndex(lemma.id) }"
        class="absolute top-full left-0 mt-px min-w-max overflow-hidden bg-gray-50 border border-border shadow-sm"
        @mousedown="bringToFront(lemma.id)">
        <div class="flex items-center justify-between gap-2 px-1.5 pt-1">
          <span :class="['text-[8px] uppercase font-bold tracking-wide', isChosen(lemma.id) ? 'bg-yellow-200 text-yellow-900 px-0.5 rounded' : 'text-text-muted']">{{ lemma.source_word }}</span>
          <button v-if="isPinned(lemma.id)"
            class="cursor-pointer text-red-500 hover:text-red-600 transition-colors"
            @click="togglePin(lemma.id)">
            <X :size="8" />
          </button>
        </div>
        <dl class="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0 p-1.5 text-[8px]">
          <dt class="text-text-muted uppercase font-bold">pos</dt><dd class="min-w-0 break-words">{{ lemma.pos_tag }}</dd>
          <dt class="text-text-muted uppercase font-bold">fine</dt><dd class="min-w-0 break-words">{{ lemma.fine_pos_tag }}</dd>
          <dt class="text-text-muted uppercase font-bold">dep</dt><dd class="min-w-0 break-words">{{ lemma.dependency_relationship }}</dd>
          <template v-if="lemma.morph.length > 0">
            <dt class="col-span-2 border-t border-border my-0.5" />
            <template v-for="attr in lemma.morph" :key="attr.key">
              <dt class="text-text-muted uppercase font-bold">{{ attr.key }}</dt><dd class="min-w-0 break-words">{{ attr.value }}</dd>
            </template>
          </template>
        </dl>
      </CollapsibleContent>
    </CollapsibleRoot>
  </div>
</template>
