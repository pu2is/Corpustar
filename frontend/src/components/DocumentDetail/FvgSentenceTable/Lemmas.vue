<script setup lang="ts">
import { ref } from 'vue'
import { Pin, X } from 'lucide-vue-next'
import { CollapsibleRoot, CollapsibleTrigger, CollapsibleContent } from 'reka-ui'
import type { LemmaItem } from '@/types/lemmatize'

defineProps<{
  lemmaTokens: LemmaItem[]
}>()

const emit = defineEmits<{
  hoverLemma: [wordIndex: number | null]
}>()

const hoverId = ref<string | null>(null)
// ordered array of pinned ids — last entry has highest z-index
const pinnedOrder = ref<string[]>([])

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
      <span class="cursor-pointer inline-flex items-center gap-0.5 px-1 py-0.5 bg-background-elevated">
        <span>{{ lemma.lemma_word }}</span>
        <CollapsibleTrigger as-child>
          <button :class="['cursor-pointer transition-colors', isPinned(lemma.id) ? 'text-violet-600' : 'text-gray-300 hover:text-gray-500']"
            @click="togglePin(lemma.id)">
            <Pin :size="8" fill="currentColor" />
          </button>
        </CollapsibleTrigger>
      </span>

      <CollapsibleContent
        :style="{ zIndex: panelZIndex(lemma.id) }"
        class="absolute top-full left-0 mt-px min-w-max bg-gray-50 border border-border shadow-sm"
        @mousedown="bringToFront(lemma.id)">
        <div class="flex items-center justify-between gap-2 px-1.5 pt-1">
          <span class="text-[8px] text-text-muted uppercase font-bold tracking-wide">{{ lemma.source_word }}</span>
          <button v-if="isPinned(lemma.id)"
            class="cursor-pointer text-text-muted hover:text-contrast-strong transition-colors"
            @click="togglePin(lemma.id)">
            <X :size="8" />
          </button>
        </div>
        <dl class="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0 p-1.5 text-[8px]">
          <dt class="text-text-muted uppercase font-bold">pos</dt><dd>{{ lemma.pos_tag }}</dd>
          <dt class="text-text-muted uppercase font-bold">fine</dt><dd>{{ lemma.fine_pos_tag }}</dd>
          <dt class="text-text-muted uppercase font-bold">morph</dt><dd>{{ lemma.morph }}</dd>
          <dt class="text-text-muted uppercase font-bold">dep</dt><dd>{{ lemma.dependency_relationship }}</dd>
        </dl>
      </CollapsibleContent>
    </CollapsibleRoot>
  </div>
</template>
