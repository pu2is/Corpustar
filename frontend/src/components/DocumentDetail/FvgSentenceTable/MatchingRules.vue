<script setup lang="ts">
import { computed, ref } from 'vue'
import { Plus } from 'lucide-vue-next'
import type { FvgItem } from '@/types/fvg'
import { useRuleFvgStore } from '@/stores/ruleFvgStore'

const props = defineProps<{
  entries: FvgItem[]
  loading: boolean
  modelValue: string | null
  ruleId: string | null
  verbLemma: string
}>()

const emit = defineEmits<{
  'update:modelValue': [id: string | null]
  'added': []
}>()

const ruleFvgStore = useRuleFvgStore()

const phrase = ref('')
const submitting = ref(false)

const canSubmit = computed(() => Boolean(props.ruleId && props.verbLemma && phrase.value.trim() && !submitting.value))

async function addRule(): Promise<void> {
  if (!canSubmit.value || !props.ruleId) return
  submitting.value = true
  try {
    await ruleFvgStore.addFvgRule({
      ruleId: props.ruleId,
      verb: props.verbLemma,
      phrase: phrase.value.trim(),
    })
    phrase.value = ''
    emit('added')
  } finally {
    submitting.value = false
  }
}

const sortedEntries = computed(() =>
  [...props.entries].sort((a, b) => a.noun.localeCompare(b.noun)),
)
</script>

<template>
  <div class="flex flex-col space-y-1">
    <!-- sticky header -->
    <p class="text-[9px] uppercase font-bold tracking-widest text-violet-300 shrink-0">Matching FVG Rules</p>

    <div v-if="loading" class="text-[10px] text-violet-400 py-1">Loading…</div>
    <div v-else-if="entries.length === 0" class="text-[10px] text-violet-400 italic py-1">No matching entries</div>
    <template v-else>
      <!-- table header (not scrollable) -->
      <table class="w-full text-[10px] border-collapse shrink-0">
        <thead>
          <tr class="text-violet-300 border-b border-violet-600">
            <th class="text-start py-1 pr-2 font-medium w-4"></th>
            <th class="text-start py-1 pr-2 font-medium">Verb</th>
            <th class="text-start py-1 pr-2 font-medium">Noun</th>
            <th class="text-start py-1 font-medium">Prep</th>
          </tr>
        </thead>
      </table>
      <!-- scrollable rows -->
      <div class="overflow-y-auto max-h-[200px]">
        <table class="w-full text-[10px] border-collapse">
          <tbody>
            <tr v-for="entry in sortedEntries"
              :key="entry.id"
              class="cursor-pointer border-b border-violet-700/50 transition-colors"
              :class="modelValue === entry.id ? 'bg-yellow-400/20 text-yellow-200' : 'text-yellow-400 hover:bg-violet-700/50'"
              @click="emit('update:modelValue', entry.id)">
              <td class="py-1 pr-2 w-4">
                <span class="inline-block w-2.5 h-2.5 rounded-full border"
                  :class="modelValue === entry.id ? 'bg-yellow-300 border-yellow-300' : 'border-violet-400'" />
              </td>
              <td class="py-1 pr-2">{{ entry.verb }}</td>
              <td class="py-1 pr-2">{{ entry.noun }}</td>
              <td class="py-1">{{ entry.prep }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- add rule footer -->
    <div class="mt-2 pt-2 border-t border-violet-600 flex items-center gap-1">
      <input
        v-model="phrase"
        type="text"
        :placeholder="`phrase for ${verbLemma}…`"
        class="flex-1 min-w-0 h-7 bg-violet-700/50 border border-violet-500 px-2 text-[10px] text-yellow-200 placeholder:text-violet-400 outline-none focus:border-violet-300"
        @keydown.enter.prevent="void addRule()">
      <button
        type="button"
        class="shrink-0 inline-flex items-center justify-center h-7 px-2 bg-yellow-400/20 text-yellow-300 transition-colors"
        :class="canSubmit ? 'hover:bg-yellow-400/40 cursor-pointer' : 'opacity-40 cursor-not-allowed'"
        :disabled="!canSubmit"
        @click="void addRule()">
        <Plus class="h-3 w-3" />
      </button>
    </div>
  </div>
</template>
