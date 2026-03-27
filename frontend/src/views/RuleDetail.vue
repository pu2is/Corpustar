<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
// components
import TopNav from '@/components/Nav/TopNav.vue';
import RuleDetailHeader from '@/components/RuleDetail/Widgets/RuleDetailHeader.vue'
import { useRuleFvgStore } from '@/stores/ruleFvgStore'
// icons
import { ChevronLeft } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const ruleFvgStore = useRuleFvgStore()

async function fetchFvgRulesByRouteId(): Promise<void> {
  const ruleId = typeof route.params.id === 'string' ? route.params.id : ''

  if (!ruleId) {
    ruleFvgStore.setActiveRuleId('')
    return
  }

  await ruleFvgStore.getAllFvgRuleByRuleId(ruleId)
}

function backToRules(): void {
  void router.push('/rules')
}

onMounted(() => {
  void fetchFvgRulesByRouteId()
})

watch(
  () => route.params.id,
  () => {
    void fetchFvgRulesByRouteId()
  }
)

</script>

<template>
  <main class="-mx-16 flex h-full flex-col overflow-hidden">
    <header class="relative flex min-h-16 items-center justify-between gap-4 bg-primary px-6 py-4 text-contrast shadow-sm">
      <TopNav />
    </header>
    <section class="ml-16 min-h-0 flex flex-1 flex-col overflow-hidden p-6 px-16">
      <!-- NavBack -->
      <button type="button"
        class="mb-4 inline-flex shrink-0 cursor-pointer items-center gap-2 text-sm font-medium text-text-muted transition-colors hover:text-violet-950"
         @click="backToRules">
        <ChevronLeft class="h-4 w-4" />
        Back to rules
      </button>
      <!-- Rule Detail Header -->
      <RuleDetailHeader />
      
    </section>
  </main>
</template>
