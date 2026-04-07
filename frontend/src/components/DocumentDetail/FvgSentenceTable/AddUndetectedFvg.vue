<script setup lang="ts">
import { ref, watch } from 'vue'
import { X } from 'lucide-vue-next'
import type { LemmaItem } from '@/types/lemmatize'
import type { FvgItem } from '@/types/fvg'
import { useRuleFvgStore } from '@/stores/ruleFvgStore'
import { useFvgCandidateStore } from '@/stores/fvgCandidate'
import MatchingRules from '@/components/DocumentDetail/FvgSentenceTable/MatchingRules.vue'

const props = defineProps<{
  pair: { verb: LemmaItem; noun: LemmaItem; adp?: LemmaItem } | null
  isOpen: boolean
  ruleId: string | null
  sentenceId: string | null
  processId: string | null
}>()

const emit = defineEmits<{ close: [] }>()

const fvgCandidateStore = useFvgCandidateStore()

const ruleFvgStore = useRuleFvgStore()
const matchingEntries = ref<FvgItem[]>([])
const selectedEntryId = ref<string | null>(null)
const loading = ref(false)

watch(() => props.isOpen, async (open) => {
  if (!open) {
    selectedEntryId.value = null
    matchingEntries.value = []
    return
  }
  if (!props.ruleId || !props.pair) return
  loading.value = true
  try {
    matchingEntries.value = await ruleFvgStore.getFvgByVerb(props.ruleId, props.pair.verb.lemma_word)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <!-- Modal only -->
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="isOpen && pair"
        class="fixed inset-0 z-50 flex items-center justify-center bg-violet-300/40"
        @click.self="emit('close')">
        <div class="bg-violet-800 text-yellow-300 shadow-2xl w-[480px] overflow-hidden">

          <!-- header -->
          <div class="flex items-center justify-between px-4 py-3 border-b border-violet-600">
            <span class="text-xs font-bold uppercase tracking-widest text-yellow-200">New FVG Entry</span>
            <button class="text-yellow-400 hover:text-yellow-200 transition-colors" @click="emit('close')">
              <X :size="14" />
            </button>
          </div>

          <!-- body -->
          <div class="p-4 space-y-4 text-xs">
            <!-- verb -->
            <div class="space-y-0.5">
              <p class="text-[9px] uppercase font-bold tracking-widest text-violet-300">Verb</p>
              <p class="font-bold text-yellow-200 text-sm">{{ pair.verb.lemma_word }}</p>
              <p class="text-yellow-500 text-[10px]">{{ pair.verb.source_word }}
                <span class="ml-1 text-violet-400">{{ pair.verb.pos_tag }} · {{ pair.verb.dependency_relationship }}</span>
              </p>
            </div>

            <!-- noun -->
            <div class="space-y-0.5">
              <p class="text-[9px] uppercase font-bold tracking-widest text-violet-300">Noun</p>
              <p class="font-bold text-yellow-200 text-sm">{{ pair.noun.lemma_word }}</p>
              <p class="text-yellow-500 text-[10px]">{{ pair.noun.source_word }}
                <span class="ml-1 text-violet-400">{{ pair.noun.pos_tag }} · {{ pair.noun.dependency_relationship }}</span>
              </p>
            </div>

            <!-- adp (optional) -->
            <div v-if="pair.adp" class="space-y-0.5">
              <p class="text-[9px] uppercase font-bold tracking-widest text-violet-300">Preposition</p>
              <p class="font-bold text-yellow-200 text-sm">{{ pair.adp.lemma_word }}</p>
              <p class="text-yellow-500 text-[10px]">{{ pair.adp.source_word }}
                <span class="ml-1 text-violet-400">{{ pair.adp.pos_tag }} · {{ pair.adp.dependency_relationship }}</span>
              </p>
            </div>

            <!-- matching fvg entries -->
            <MatchingRules :entries="matchingEntries"
              :loading="loading" v-model="selectedEntryId" />
          </div>

          <!-- footer -->
          <div class="flex justify-end gap-2 px-4 py-3 border-t border-violet-600">
            <button class="text-[10px] px-3 py-1.5 text-yellow-400 hover:text-yellow-200 transition-colors"
              @click="emit('close')">Cancel</button>
            <button
              class="text-[10px] px-3 py-1.5 bg-yellow-400 text-violet-900 font-bold transition-colors"
              :class="selectedEntryId ? 'hover:bg-yellow-300 cursor-pointer' : 'opacity-40 cursor-not-allowed'"
              :disabled="!selectedEntryId"
              @click="async () => {
                if (!selectedEntryId || !sentenceId || !processId || !pair) return
                await fvgCandidateStore.addFvgCandidate(
                  sentenceId,
                  processId,
                  selectedEntryId,
                  pair.verb.id,
                  pair.noun.id,
                  pair.adp?.id ?? '',
                )
                emit('close')
              }">
              Add Entry
            </button>
          </div>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.15s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>