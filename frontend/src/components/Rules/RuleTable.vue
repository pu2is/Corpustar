<script setup lang="ts">
import { computed } from 'vue'
import { ChevronRight, Trash2 } from 'lucide-vue-next'
import type { RuleItem } from '@/types/rules'

const props = defineProps<{
  ruleItems: RuleItem[]
}>()

const fileNameByRuleId = computed(() => {
  const names = new Map<RuleItem['id'], string>()

  for (const rule of props.ruleItems) {
    const fileNameWithExtension = rule.path.split(/[\\/]/).pop() ?? ''
    const extensionIndex = fileNameWithExtension.lastIndexOf('.')
    const fileName = extensionIndex > 0
      ? fileNameWithExtension.slice(0, extensionIndex)
      : fileNameWithExtension

    names.set(rule.id, fileName)
  }

  return names
})
</script>

<template>
  <div class="scroll-area min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
    <article v-for="rule in ruleItems"
      :key="rule.id"
      class="bg-background-elevated/60 p-4 text-[0.84rem] font-medium text-text-muted transition-colors hover:bg-background-elevated flex items-center justify-between gap-3">
      <div class="min-w-0">
        <div class="truncate text-[0.84rem] text-violet-950">
          {{ fileNameByRuleId.get(rule.id) }}
        </div>
        <div class="mt-0.5 text-[0.72rem] font-normal uppercase tracking-[0.04em] text-text-muted/80">
          {{ rule.type }}
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button type="button"
          class="inline-flex items-center cursor-pointer justify-center rounded p-1 text-text-muted/70 transition-colors hover:text-error"
          aria-label="Delete rule">
          <Trash2 class="h-4 w-4 shrink-0" />
        </button>
        <button type="button"
          class="inline-flex cursor-pointer items-center justify-center rounded p-1 text-text-muted/70 transition-colors hover:text-violet-950"
          aria-label="Open rule">
          <ChevronRight class="h-4 w-4 shrink-0" />
        </button>
      </div>
    </article>
  </div>
</template>
