<script setup lang="ts">
import { computed } from 'vue'
import { PencilRuler, TextSearch } from 'lucide-vue-next'
import {
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuPortal,
  DropdownMenuRoot,
  DropdownMenuTrigger,
} from 'reka-ui'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const normalizedPath = computed(() => route.path.replace(/\/+$/, ''))

const isAnalyzeRoute = computed(() => {
  return normalizedPath.value === '/analyze' || /^\/analyze\/[^/]+$/.test(normalizedPath.value)
})
const isRulesRoute = computed(() => normalizedPath.value === '/rules')

const triggerLabel = computed(() => (isRulesRoute.value ? 'Rules' : 'Analyze'))
const triggerIcon = computed(() => (isRulesRoute.value ? PencilRuler : TextSearch))

const menuLabel = computed(() => (isAnalyzeRoute.value ? 'Rules' : 'Analyze'))
const menuTarget = computed(() => (isAnalyzeRoute.value ? '/rules' : '/analyze'))
const menuIcon = computed(() => (isAnalyzeRoute.value ? PencilRuler : TextSearch))

function navigateToTarget(): void {
  void router.push(menuTarget.value)
}
</script>

<template>
  <DropdownMenuRoot>
    <DropdownMenuTrigger as-child>
      <div role="button"
        tabindex="0"
        :aria-label="`Open ${triggerLabel} menu`"
        class="inline-flex cursor-pointer items-center gap-3 p-0 text-contrast outline-none focus:outline-none focus-visible:outline-none">
        <component :is="triggerIcon" class="h-5 w-5 shrink-0" />
        <h1 class="text-2xl font-semibold tracking-tight text-contrast">
          {{ triggerLabel }}
        </h1>
      </div>
    </DropdownMenuTrigger>

    <DropdownMenuPortal>
      <DropdownMenuContent :side-offset="8"
        class="min-w-36 rounded-none border border-border bg-contrast p-1 text-contrast-strong shadow-lg">
        <DropdownMenuItem
          class="flex cursor-pointer items-center gap-2 rounded-none px-3 py-2 text-sm font-medium outline-none data-[highlighted]:bg-secondary-soft"
          @select="navigateToTarget">
          <component :is="menuIcon" class="h-4 w-4 shrink-0" />
          {{ menuLabel }}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenuPortal>
  </DropdownMenuRoot>
</template>
