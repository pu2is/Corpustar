<script setup lang="ts">
import { computed } from 'vue'
// composables
import { getIdFromUrl } from '@/composables/useRouteId'
// stores
import { useRuleStore } from '@/stores/ruleStore'
import { useRuleFvgStore } from '@/stores/ruleFvgStore'
// icons
import { Table2 } from 'lucide-vue-next'

const ruleId = getIdFromUrl()
const ruleStore = useRuleStore()
const ruleFvgStore = useRuleFvgStore()

const ruleFileName = computed(() => ruleStore.getRuleNameById(ruleId.value))
const rowsCount = computed(() => ruleFvgStore.fvg.length)
</script>

<template>
  <header class="space-y-1 py-3">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h2 class="text-xl font-semibold text-violet-950">
        {{ ruleFileName }}
      </h2>
    </div>

    <p class="inline-flex items-center gap-2 px-2 py-1 text-sm">
      <Table2 class="h-3.5 w-3.5" />
      {{ rowsCount }} Rows
    </p>
  </header>
</template>
