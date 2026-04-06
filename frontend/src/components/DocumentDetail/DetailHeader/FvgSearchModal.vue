<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  DialogContent, DialogOverlay, DialogPortal, DialogRoot, DialogTrigger, DialogClose,
  DropdownMenuContent, DropdownMenuItem, DropdownMenuPortal, DropdownMenuRoot, DropdownMenuTrigger,
} from 'reka-ui'
import { ChevronDown, Check } from 'lucide-vue-next'
// stores
import { useRuleStore } from '@/stores/ruleStore'
import { useProcessStore } from '@/stores/processStore'

const props = defineProps<{
  segmentationId: string | null
}>()

const open = ref(false)
const router = useRouter()
const ruleStore = useRuleStore()
const processStore = useProcessStore()

const rules = computed(() => ruleStore.rules)

const selectedRuleId = ref<string | null>(null)
const selectedRuleName = computed(() =>
  selectedRuleId.value ? ruleStore.getRuleNameById(selectedRuleId.value) : 'Choose rule',
)

function confirmFvgSearch(): void {
  if (!selectedRuleId.value || !props.segmentationId) return
  processStore.fvgSearchRunning = true
  void processStore.fvgMatch(props.segmentationId, selectedRuleId.value)
  open.value = false
  void router.push('/')
}
</script>

<template>
  <DialogRoot v-model:open="open">
    <DialogTrigger as-child>
      <button type="button"
        class="cursor-pointer text-violet-600 px-3 py-1.5 text-sm font-medium bg-yellow-300 transition hover:bg-yellow-400 disabled:cursor-not-allowed disabled:opacity-60">
        Start FVG search
      </button>
    </DialogTrigger>

    <DialogPortal>
      <DialogOverlay class="fixed inset-0 z-40 bg-violet-200/40" />
      <DialogContent
        class="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 bg-violet-700 p-8 shadow-xl focus:outline-none">
        <h2 class="mb-4 text-lg font-semibold text-yellow-300">Start FVG search</h2>

        <!-- Choose rule -->
        <div class="mb-6">
          <label class="mb-1.5 block text-xs font-medium uppercase tracking-widest text-yellow-100/60">
            Choose rule
          </label>
          <DropdownMenuRoot>
            <DropdownMenuTrigger as-child>
              <button type="button"
                class="inline-flex w-full items-center justify-between border border-violet-400 px-3 py-1.5 text-sm text-yellow-300 outline-none transition hover:border-yellow-300">
                <span class="truncate">{{ selectedRuleName }}</span>
                <ChevronDown class="ml-2 h-4 w-4 shrink-0" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuPortal>
              <DropdownMenuContent :side-offset="4" align="start"
                class="z-[60] w-[--reka-dropdown-menu-trigger-width] border border-border bg-violet-800 p-0.5 shadow-md">
                <DropdownMenuItem
                  v-for="rule in rules"
                  :key="rule.id"
                  class="flex w-full cursor-pointer items-center justify-between px-3 py-1.5 text-sm outline-none data-[highlighted]:bg-violet-700"
                  :class="selectedRuleId === rule.id ? 'text-yellow-300' : 'text-yellow-100/70'"
                  @select="selectedRuleId = rule.id">
                  <span class="truncate">{{ ruleStore.getRuleNameById(rule.id) }}</span>
                  <Check v-if="selectedRuleId === rule.id" class="ml-2 h-3.5 w-3.5 shrink-0" />
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenuPortal>
          </DropdownMenuRoot>
        </div>
        
        <div class="flex items-center justify-end gap-2">
          <DialogClose as-child>
            <button type="button"
              class="cursor-pointer bg-violet-500 px-3 py-1.5 text-sm font-medium text-yellow-300 transition hover:bg-violet-600">
              Cancel
            </button>
          </DialogClose>
          <button type="button"
            :disabled="!selectedRuleId"
            class="cursor-pointer bg-yellow-300 px-3 py-1.5 text-sm font-medium text-violet-700 transition hover:bg-yellow-400 disabled:cursor-not-allowed disabled:opacity-40"
            @click="confirmFvgSearch()">
            Start
          </button>
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>