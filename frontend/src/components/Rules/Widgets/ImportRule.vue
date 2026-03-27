<script setup lang="ts">
import { Plus } from 'lucide-vue-next'
import { ref } from 'vue'

import { useRuleStore } from '@/stores/ruleStore'

const ruleStore = useRuleStore()
const importing = ref(false)

async function openFilePicker(): Promise<void> {
  if (importing.value) {
    return
  }

  if (!window.electronAPI?.selectRuleFile) {
    return
  }

  importing.value = true
  try {
    const filePath = await window.electronAPI.selectRuleFile()
    if (!filePath) {
      return
    }

    await ruleStore.importRule({
      path: filePath,
      type: 'fvg',
    })
  } catch {
    // store handles error state
  } finally {
    importing.value = false
  }
}
</script>

<template>
  <div class="absolute inset-0 pointer-events-none">
    <div class="absolute right-6 top-1/2 z-20 -translate-y-1/2 pointer-events-auto">
      <button type="button"
        class="inline-flex cursor-pointer h-10 w-10 items-center justify-center rounded-full border-0 bg-contrast p-0 text-primary shadow-md transition hover:bg-secondary-soft hover:text-primary"
        :disabled="importing"
        aria-label="Import rule file"
        title="Import rule file"
        @click="openFilePicker">
        <Plus class="h-5 w-5 shrink-0" />
      </button>
    </div>
  </div>
</template>
