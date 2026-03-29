<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
// icons
import { Trash2 } from 'lucide-vue-next'
// components
import AddFvgRow from '@/components/RuleDetail/Widgets/AddFvgRow.vue'
import SearchBar from '@/components/RuleDetail/Widgets/SearchBar.vue'
// stores
import { useRuleFvgStore } from '@/stores/ruleFvgStore'
// types
import type { FvgItem } from '@/types/fvg'

const ruleFvgStore = useRuleFvgStore()

const searchValue = ref('')
const scrollAreaRef = ref<HTMLDivElement | null>(null)
const scrollTop = ref(0)
const viewportHeight = ref(0)

const ROW_HEIGHT = 44
const OVERSCAN_ROWS = 10

let resizeObserver: ResizeObserver | null = null

const normalizedSearchValue = computed(() => searchValue.value.trim().toLowerCase())

const filteredRules = computed<FvgItem[]>(() => {
  if (!normalizedSearchValue.value) {
    return ruleFvgStore.fvg
  }

  return ruleFvgStore.fvg.filter((item: FvgItem) => {
    const verb = item.verb.toLowerCase()
    const phrase = item.phrase.toLowerCase()
    return verb.includes(normalizedSearchValue.value) || phrase.includes(normalizedSearchValue.value)
  })
})

const totalRows = computed(() => filteredRules.value.length)
const visibleStartIndex = computed(() => {
  return Math.max(0, Math.floor(scrollTop.value / ROW_HEIGHT) - OVERSCAN_ROWS)
})
const visibleRowCount = computed(() => {
  const rowsInViewport = Math.ceil(viewportHeight.value / ROW_HEIGHT)
  return Math.max(1, rowsInViewport + OVERSCAN_ROWS * 2)
})
const visibleEndIndex = computed(() => {
  return Math.min(totalRows.value, visibleStartIndex.value + visibleRowCount.value)
})
const visibleRules = computed(() => {
  return filteredRules.value.slice(visibleStartIndex.value, visibleEndIndex.value)
})
const topSpacerHeight = computed(() => visibleStartIndex.value * ROW_HEIGHT)
const bottomSpacerHeight = computed(() => Math.max(0, (totalRows.value - visibleEndIndex.value) * ROW_HEIGHT))
const virtualPaddingStyle = computed(() => {
  return {
    paddingTop: `${topSpacerHeight.value}px`,
    paddingBottom: `${bottomSpacerHeight.value}px`,
  }
})

function updateViewportHeight(): void {
  viewportHeight.value = scrollAreaRef.value?.clientHeight ?? 0
}

function handleScroll(): void {
  scrollTop.value = scrollAreaRef.value?.scrollTop ?? 0
}

function getDisplayIndex(localIndex: number): number {
  return visibleStartIndex.value + localIndex + 1
}

async function removeFvgRuleById(fvgRuleId: string): Promise<void> {
  await ruleFvgStore.removerFvgRule(fvgRuleId)
}

watch(searchValue, () => {
  const scrollEl = scrollAreaRef.value
  if (!scrollEl) {
    return
  }

  scrollEl.scrollTop = 0
  scrollTop.value = 0
})

watch(totalRows, () => {
  const scrollEl = scrollAreaRef.value
  if (!scrollEl) {
    return
  }

  const maxScrollTop = Math.max(0, totalRows.value * ROW_HEIGHT - viewportHeight.value)
  if (scrollEl.scrollTop > maxScrollTop) {
    scrollEl.scrollTop = maxScrollTop
    scrollTop.value = maxScrollTop
  }
})

onMounted(() => {
  updateViewportHeight()
  const scrollEl = scrollAreaRef.value
  if (!scrollEl) {
    return
  }

  resizeObserver = new ResizeObserver(() => {
    updateViewportHeight()
  })

  resizeObserver.observe(scrollEl)
})

onBeforeUnmount(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
})
</script>

<template>
  <section class="min-h-0 flex flex-1 flex-col overflow-hidden bg-background-elevated/20">
    <!-- Header -->
    <SearchBar v-model="searchValue"
      :matches="totalRows" />
    <!-- Content -->
    <div ref="scrollAreaRef"
      class="scroll-area min-h-0 flex-1 overflow-y-auto"
      @scroll.passive="handleScroll">
      <!-- Empty state -->
      <p v-if="totalRows === 0"
        class="px-3 py-6 text-sm text-text-muted">
        No FVG rows found.
      </p>
      <!-- Fvg Candidates table -->
      <div v-else 
        :style="virtualPaddingStyle">
        <article v-for="(item, index) in visibleRules"
          :key="item.id"
          class="grid items-center gap-3 border-b border-secondary/10 px-3 text-sm text-violet-950"
          :style="{ height: `${ROW_HEIGHT}px`, gridTemplateColumns: '52px minmax(0, 1fr) minmax(0, 3fr) 40px' }">
          <span class="text-xs tabular-nums text-text-muted">
            {{ getDisplayIndex(index) }}
          </span>
          <span class="truncate font-medium">
            {{ item.verb }}
          </span>
          <span class="truncate text-text-muted">
            {{ item.phrase }}
          </span>
          <!-- Action: delete -->
          <button type="button"
            class="inline-flex cursor-pointer items-center justify-center rounded p-1 text-text-muted/70 transition-colors hover:text-error"
            aria-label="Remove FVG rule"
            @click="void removeFvgRuleById(item.id)">
            <Trash2 class="h-4 w-4 shrink-0" />
          </button>
        </article>
      </div>
    </div>
    <!-- Footer -->
    <AddFvgRow />
  </section>
</template>
