<script setup lang="ts">
import { useRouter } from 'vue-router'
// icons
import { ChevronRight, Trash2 } from 'lucide-vue-next'
// stores
import { useRuleStore } from '@/stores/ruleStore'
// types
import type { RuleItem } from '@/types/rules'
import { APP_ROUTES } from '@/config/routes'

const props = defineProps<{
  ruleItems: RuleItem[]
}>()

const ruleStore = useRuleStore()
const router = useRouter()

async function removeRuleItem(event: MouseEvent, ruleId: string): Promise<void> {
  event.stopPropagation()
  await ruleStore.removeRuleById(ruleId)
}

function openRuleDetail(event: MouseEvent, ruleId: string): void {
  event.stopPropagation()
  void router.push(APP_ROUTES.ruleDetail(ruleId))
}
</script>

<template>
  <div class="scroll-area min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
    <article v-for="rule in ruleItems"
      :key="rule.id"
      class="bg-background-elevated/60 p-4 text-[0.84rem] font-medium text-text-muted transition-colors hover:bg-background-elevated flex items-center justify-between gap-3">
      <div class="min-w-0">
        <div class="truncate text-[0.84rem] text-violet-950">
          {{ ruleStore.getRuleNameById(rule.id) }}
        </div>
        <div class="mt-0.5 text-[0.72rem] font-normal uppercase tracking-[0.04em] text-text-muted/80">
          {{ rule.type }}
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button type="button"
          class="inline-flex items-center cursor-pointer justify-center rounded p-1 text-text-muted/70 transition-colors hover:text-error"
          aria-label="Delete rule"
          @click="(event) => void removeRuleItem(event, rule.id)">
          <Trash2 class="h-4 w-4 shrink-0" />
        </button>
        <button type="button"
          class="inline-flex cursor-pointer items-center justify-center rounded p-1 text-text-muted/70 transition-colors hover:text-violet-950"
          aria-label="Open rule"
          @click="(event) => openRuleDetail(event, rule.id)">
          <ChevronRight class="h-4 w-4 shrink-0" />
        </button>
      </div>
    </article>
  </div>
</template>
