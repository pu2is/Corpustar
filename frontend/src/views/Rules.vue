<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
// components
import RuleTable from '@/components/Rules/RuleTable.vue'
import RulesNavigation from '@/components/Rules/Widgets/RulesNavigation.vue'
import RuleTableHeader from '@/components/Rules/Widgets/RuleTableHeader.vue'
// stores
import { useRuleStore } from '@/stores/ruleStore'

const ruleStore = useRuleStore()
const { rules } = storeToRefs(ruleStore)

const ruleItems = computed(() => rules.value)
const hasRuleItems = computed(() => ruleItems.value.length > 0)
</script>

<template>
  <section class="-mx-16">
    
    <!-- Header / Navigation -->
    <RulesNavigation />

    <!-- Content / Empty State -->
    <div class="min-h-0 flex flex-1 flex-col gap-3 p-6 px-16 ml-16">
      <RuleTableHeader />

      <p v-if="!hasRuleItems"
        class="m-0 px-2 py-1 text-sm text-text-muted">
        No rule items found.
      </p>

      <RuleTable v-else />
    </div>
  </section>
</template>
