<script setup lang="ts">
import { computed } from 'vue'
// icons
import { RefreshCcw } from 'lucide-vue-next'
// stores
import { useRuleStore } from '@/stores/ruleStore'

const ruleStore = useRuleStore()
const ruleCount = computed(() => ruleStore.rules.length)

function refreshRules(): void {
  void ruleStore.getAllRules()
}
</script>

<template>
  <header class="shrink-0 flex items-end justify-between gap-3">
    <div class="flex items-start gap-2.5">
      <div class="flex-col cursor-default select-none">
        <h2 class="m-0 text-[0.95rem] font-semibold tracking-[0.01em] text-violet-950">
          Rules
        </h2>
        <p class="mt-0.5 text-xs text-text-muted">
          {{ ruleCount }} item{{ ruleCount === 1 ? '' : 's' }}
        </p>
      </div>

      <button type="button"
        class="inline-flex cursor-pointer items-center justify-center rounded-full bg-secondary/5 p-2 text-text-muted transition-colors hover:bg-secondary/20"
        aria-label="Refresh rules"
        title="Refresh rules"
        @click="refreshRules">
        <RefreshCcw class="size-4" />
      </button>
    </div>
  </header>
</template>
