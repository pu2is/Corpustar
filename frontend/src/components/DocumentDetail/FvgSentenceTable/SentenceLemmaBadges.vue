<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { Circle, CircleDot, Pencil } from 'lucide-vue-next'
import { CollapsibleRoot, CollapsibleContent } from 'reka-ui'
import { useFvgCandidateStore } from '@/stores/fvgCandidate'
import EditLemmaModal from '@/components/DocumentDetail/Modals/EditLemmaModal.vue'

const props = defineProps<{
  sentenceId: string
  clearSignal?: number
}>()

const emit = defineEmits<{
  hoverLemma: [wordIndex: number | null]
  chosenIndices: [wordIndices: number[]]
}>()

const fvgStore = useFvgCandidateStore()
const lemmaTokens = computed(() =>
  fvgStore.sentenceFvgList.find((s) => s.id === props.sentenceId)?.lemma_tokens ?? []
)

const hoverId = ref<string | null>(null)
const editingLemmaId = ref<string | null>(null)

// Lemma info details panel
watch(() => props.clearSignal, () => {
  chosenIds.value = new Set()
})

function isDetailOpen(id: string): boolean {
  return hoverId.value === id
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
  const wordIndices = lemmaTokens.value
    .filter((l) => next.has(l.id))
    .map((l) => l.word_index)
  emit('chosenIndices', wordIndices)
}

const MUTED_POS_TAGS = ['PRON', 'PROPN', 'DET', 'PUNCT', 'SPACE', 'SYM', 'X', 'ADV']

function badgeClass(posTag: string): string {
  if (posTag === 'ADP') return 'bg-purple-200/50 text-violet-700'
  if (posTag === 'VERB') return 'bg-amber-50 text-amber-700'
  if (posTag === 'NOUN') return 'bg-blue-50 text-blue-600'
  if (MUTED_POS_TAGS.includes(posTag)) return 'bg-background-elevated text-gray-300'
  return 'bg-background-elevated text-gray-500'
}

function badgeTextClass(posTag: string): string {
  if (posTag === 'ADP') return 'text-violet-700'
  if (posTag === 'VERB') return 'text-amber-700'
  if (posTag === 'NOUN') return 'text-blue-600'
  if (MUTED_POS_TAGS.includes(posTag)) return 'text-gray-300'
  return 'text-gray-500'
}
</script>

<template>
  <div class="flex flex-wrap gap-2 text-xs text-text-muted">
    <CollapsibleRoot v-for="lemma in lemmaTokens"
      :key="lemma.id"
      :open="isDetailOpen(lemma.id)"
      class="relative"
      @mouseenter="hoverId = lemma.id; emit('hoverLemma', lemma.word_index)"
      @mouseleave="hoverId = null; emit('hoverLemma', null)">
      <div class="flex gap-1 cursor-pointer inline-flex items-center gap-0.5 px-1 py-0.5"
        :class="badgeClass(lemma.pos_tag)"
        @click="toggleChosen(lemma.id)">
        
        <span class="flex-shrink-0 transition-colors"
          :class="isChosen(lemma.id) ? badgeTextClass(lemma.pos_tag) : 'text-gray-300'">
          <CircleDot v-if="isChosen(lemma.id)" :size="9" />
          <Circle v-else :size="9" />
        </span>
        
        <span :class="isChosen(lemma.id) ? 'font-bold select-none' : 'select-none'">
          {{ lemma.lemma_word }}
        </span>

        <button class="ms-1 flex-shrink-0 transition-colors cursor-pointer"
          :class="badgeTextClass(lemma.pos_tag)"
          @click.stop="editingLemmaId = lemma.id">
          <Pencil :size="10" />
        </button>
        
      </div>

      <CollapsibleContent
        class="absolute top-full left-0 mt-px min-w-max w-full overflow-hidden bg-gray-50 border border-border shadow-sm"
        style="z-index: 20">
        <div class="px-1.5 pt-1">
          <span :class="['text-[10px] uppercase font-bold tracking-wide', isChosen(lemma.id) ? 'bg-yellow-200 text-yellow-900 px-0.5 rounded' : 'text-text-muted']">{{ lemma.source_word }}</span>
        </div>
        <dl class="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0 p-1.5 text-[10px]">
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

  <EditLemmaModal :lemma-id="editingLemmaId"
    @close="editingLemmaId = null" />
</template>
