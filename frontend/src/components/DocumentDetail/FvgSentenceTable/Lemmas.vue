<script setup lang="ts">
import { ref, watch } from 'vue'
import { Pin, X } from 'lucide-vue-next'
import { CollapsibleRoot, CollapsibleTrigger, CollapsibleContent } from 'reka-ui'
import type { LemmaItem } from '@/types/lemmatize'

const props = defineProps<{
  lemmaTokens: LemmaItem[]
  isActive: boolean
}>()

const emit = defineEmits<{
  hoverLemma: [wordIndex: number | null]
  pinned: []
}>()

const hoverId = ref<string | null>(null)
// ordered array of pinned ids — last entry has highest z-index
const pinnedOrder = ref<string[]>([])

watch(() => props.isActive, (active) => {
  if (!active) pinnedOrder.value = []
})

function isPinned(id: string): boolean {
  return pinnedOrder.value.includes(id)
}

function isOpen(id: string): boolean {
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

function panelZIndex(id: string): number {
  if (hoverId.value === id && !isPinned(id)) return 20
  const idx = pinnedOrder.value.indexOf(id)
  return idx !== -1 ? 10 + idx : 10
}
</script>

<template>
  <div class="flex flex-wrap gap-1 text-xs text-text-muted">
    <CollapsibleRoot v-for="lemma in lemmaTokens"
      :key="lemma.id"
      :open="isOpen(lemma.id)"
      class="relative"
      @mouseenter="hoverId = lemma.id; emit('hoverLemma', lemma.word_index)"
      @mouseleave="hoverId = null; emit('hoverLemma', null)">
      <span :class="[
          'cursor-pointer inline-flex items-center gap-0.5 px-1 py-0.5',
          lemma.pos_tag === 'VERB' ? 'bg-background-elevated text-violet-700' :
          lemma.pos_tag === 'NOUN' ? 'bg-amber-50 text-amber-700' :
          lemma.pos_tag === 'ADP'  ? 'bg-blue-50 text-blue-600' :
          ['PRON', 'PROPN', 'DET', 'PUNCT', 'SPACE', 'SYM', 'X', 'ADV'].includes(lemma.pos_tag)
            ? 'bg-background-elevated text-gray-300' :
          'bg-background-elevated text-gray-500'
        ]">
        <span>{{ lemma.lemma_word }}</span>
        <CollapsibleTrigger as-child>
          <button :class="['cursor-pointer transition-colors', isPinned(lemma.id) ? 'text-yellow-500' : 'text-gray-300 hover:text-gray-500']"
            @click="togglePin(lemma.id)">
            <Pin :size="8" fill="currentColor" />
          </button>
        </CollapsibleTrigger>
      </span>

      <CollapsibleContent
        :style="{ zIndex: panelZIndex(lemma.id) }"
        class="absolute top-full left-0 mt-px min-w-max overflow-hidden bg-gray-50 border border-border shadow-sm"
        @mousedown="bringToFront(lemma.id)">
        <div class="flex items-center justify-between gap-2 px-1.5 pt-1">
          <span class="text-[8px] text-text-muted uppercase font-bold tracking-wide">{{ lemma.source_word }}</span>
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
