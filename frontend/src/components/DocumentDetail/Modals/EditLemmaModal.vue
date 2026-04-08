<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { X } from 'lucide-vue-next'
import { useLemmaStore } from '@/stores/lemmaStore'
import { useFvgCandidateStore } from '@/stores/fvgCandidate'

const props = defineProps<{
  lemmaId: string | null
}>()

const emit = defineEmits<{
  close: []
}>()

const lemmaStore = useLemmaStore()
const fvgStore = useFvgCandidateStore()

const lemma = computed(() => {
  if (!props.lemmaId) return undefined
  for (const s of fvgStore.sentenceFvgList) {
    const found = s.lemma_tokens.find((t) => t.id === props.lemmaId)
    if (found) return found
  }
  return undefined
})
const isOpen = computed(() => props.lemmaId !== null)

const lemmaWord = ref('')
const posTag = ref('')
const saving = ref(false)
const error = ref('')

watch(() => props.lemmaId, (id) => {
  if (!id || !lemma.value) return
  lemmaWord.value = lemma.value.lemma_word
  posTag.value = lemma.value.pos_tag
  saving.value = false
  error.value = ''
})

const isChanged = computed(() => {
  if (!lemma.value) return false
  return lemmaWord.value !== lemma.value.lemma_word || posTag.value !== lemma.value.pos_tag
})

function onLemmaWordInput(event: Event) {
  const el = event.target as HTMLInputElement
  const normalized = el.value.replace(/[^a-zA-ZäöüÄÖÜß]/g, '')
  lemmaWord.value = normalized
  el.value = normalized
}

async function save() {
  if (!props.lemmaId || !isChanged.value) {
    emit('close')
    return
  }
  saving.value = true
  error.value = ''
  try {
    await lemmaStore.editLemmaToken(props.lemmaId!, lemmaWord.value, posTag.value)
    emit('close')
  } catch {
    error.value = 'Save failed. Please try again.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="isOpen && lemma !== undefined"
        class="fixed inset-0 z-50 flex items-center justify-center bg-violet-300/40">
        <div class="bg-violet-800 text-yellow-300 shadow-2xl w-[400px] overflow-hidden">

          <!-- header -->
          <div class="flex items-center justify-between px-4 py-3 border-b border-violet-600">
            <span class="text-xs font-bold uppercase tracking-widest text-yellow-200">Edit Lemma Token</span>
            <button class="text-yellow-400 hover:text-yellow-200 transition-colors" @click="emit('close')">
              <X :size="14" />
            </button>
          </div>

          <!-- body -->
          <div class="p-4 space-y-4 text-xs">
            <!-- source word (read-only) -->
            <div class="space-y-0.5">
              <p class="text-[9px] uppercase font-bold tracking-widest text-violet-300">Source Word</p>
              <p class="font-bold text-yellow-200 text-sm">{{ lemma.source_word }}</p>
            </div>

            <!-- lemma word -->
            <div class="space-y-1">
              <label class="text-[9px] uppercase font-bold tracking-widest text-violet-300">Lemma Word</label>
              <input
                type="text"
                class="w-full bg-violet-900 border border-violet-600 text-yellow-200 px-2 py-1.5 text-xs focus:outline-none focus:border-yellow-400"
                :value="lemmaWord"
                @input="onLemmaWordInput"
                @keydown.esc="emit('close')" />
            </div>

            <!-- pos tag -->
            <div class="space-y-1">
              <label class="text-[9px] uppercase font-bold tracking-widest text-violet-300">POS Tag</label>
              <select
                v-model="posTag"
                class="w-full bg-violet-900 border border-violet-600 text-yellow-200 px-2 py-1.5 text-xs focus:outline-none focus:border-yellow-400 cursor-pointer"
                @keydown.esc="emit('close')">
                <option v-for="opt in lemmaStore.pos_options" :key="opt" :value="opt"
                  class="bg-violet-900 text-yellow-200">{{ opt }}</option>
              </select>
            </div>

            <!-- current values -->
            <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-[10px] border-t border-violet-600 pt-3">
              <span class="text-violet-400 uppercase font-bold">fine pos</span>
              <span class="text-yellow-500">{{ lemma.fine_pos_tag }}</span>
              <span class="text-violet-400 uppercase font-bold">dep</span>
              <span class="text-yellow-500">{{ lemma.dependency_relationship }}</span>
            </div>

            <!-- error -->
            <p v-if="error" class="text-[10px] text-red-400">{{ error }}</p>
          </div>

          <!-- footer -->
          <div class="flex justify-end gap-2 px-4 py-3 border-t border-violet-600">
            <button
              class="text-[10px] px-3 py-1.5 text-yellow-400 hover:text-yellow-200 transition-colors"
              @click="emit('close')">Cancel</button>
            <button
              class="text-[10px] px-3 py-1.5 bg-yellow-400 text-violet-900 font-bold hover:bg-yellow-300 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-colors"
              :disabled="saving"
              @click="save">
              {{ saving ? 'Saving…' : 'Save' }}
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
