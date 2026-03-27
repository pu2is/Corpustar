<script setup lang="ts">
import { computed, ref } from 'vue'

import { getIdFromUrl } from '@/composables/useRouteId'
import { useRuleFvgStore } from '@/stores/ruleFvgStore'

const ruleId = getIdFromUrl()
const ruleFvgStore = useRuleFvgStore()

const verb = ref('')
const phrase = ref('')
const submitting = ref(false)

const canSubmit = computed(() => {
  return Boolean(ruleId.value && verb.value.trim() && phrase.value.trim() && !submitting.value)
})

async function addFvgRow(): Promise<void> {
  if (!canSubmit.value) {
    return
  }

  submitting.value = true

  try {
    await ruleFvgStore.addFvgRule({
      ruleId: ruleId.value,
      verb: verb.value.trim(),
      phrase: phrase.value.trim(),
    })

    verb.value = ''
    phrase.value = ''
  } catch {
    // store handles error state
  } finally {
    submitting.value = false
  }
}
</script>


<template>
  <footer class="shrink-0 grid grid-cols-1 items-center gap-2 bg-background-elevated px-3 py-4 sm:grid-cols-[minmax(0,1fr)_minmax(0,2fr)_auto]">
    <input
      v-model="verb"
      type="text"
      placeholder="Verb"
      class="h-9 rounded border border-secondary/20 bg-background px-3 text-sm text-violet-950 outline-none transition-colors placeholder:text-text-muted/70 focus:border-secondary/50"
      @keydown.enter.prevent="void addFvgRow()">
    <input
      v-model="phrase"
      type="text"
      placeholder="Phrase"
      class="h-9 rounded border border-secondary/20 bg-background px-3 text-sm text-violet-950 outline-none transition-colors placeholder:text-text-muted/70 focus:border-secondary/50"
      @keydown.enter.prevent="void addFvgRow()">
    <button
      type="button"
      class="inline-flex h-9 cursor-pointer items-center justify-center rounded bg-contrast px-3 text-xs font-semibold text-primary transition-colors hover:bg-secondary-soft disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
      :disabled="!canSubmit"
      @click="void addFvgRow()">
      Add
    </button>
  </footer>
</template>
