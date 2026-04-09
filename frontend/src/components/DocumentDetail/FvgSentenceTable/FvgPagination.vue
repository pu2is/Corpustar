<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { ChevronFirst, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { useProcessStore } from '@/stores/processStore'
import { useFvgCandidateStore } from '@/stores/fvgCandidate'
import { usePaginationStore } from '@/stores/local/paginationStore'
import type { FvgSentenceTableMode } from '@/stores/local/paginationStore'
import { getIdFromUrl } from '@/composables/useRouteId'

const docId = getIdFromUrl()
const processStore = useProcessStore()
const fvgCandidateStore = useFvgCandidateStore()
const paginationStore = usePaginationStore()

const loading = ref(false)

const segmentationId = computed(() => processStore.getSentenceSegmentationProcessByDocId(docId.value)?.id ?? '')
const fvgProcessId = computed(() => processStore.getFvgProcessByDocId(docId.value)?.id ?? '')
const display = computed(() => fvgCandidateStore.display)
const cursor = computed(() => fvgCandidateStore.cursor)

function displayToMode(d: typeof fvgCandidateStore.display): FvgSentenceTableMode {
  if (d === 'detected') return 'matched'
  if (d === 'undetected') return 'unmatched'
  return 'all'
}

const currentMode = computed(() => displayToMode(display.value))
const savedCursor = computed(() => paginationStore.paginationInfo.fvgSentenceTable[currentMode.value] ?? null)
const page = computed(() => savedCursor.value?.page ?? 1)

const prevCursor = computed(() => cursor.value?.previousCursor ?? null)
const nextCursor = computed(() => cursor.value?.nextCursor ?? null)

const allowFirst = computed(() => !loading.value && page.value > 1)
const allowPrev = computed(() => !loading.value && Boolean(prevCursor.value))
const allowNext = computed(() => !loading.value && Boolean(nextCursor.value))

async function scrollToTop(): Promise<void> {
  await nextTick()
  const el = document.querySelector<HTMLElement>('[data-fvg-sentence-scroll-area]')
  if (el) el.scrollTop = 0
}

function saveCursor(page: number): void {
  paginationStore.savePagination({
    section: 'fvgSentenceTable',
    cursor: {
      ...paginationStore.paginationInfo.fvgSentenceTable,
      [currentMode.value]: {
        currentCursor: cursor.value?.currentCursor ?? null,
        nextCursor: cursor.value?.nextCursor ?? null,
        page,
      },
    },
  })
}

async function fetchPage(cursor: string | null): Promise<void> {
  if (!segmentationId.value) return
  const verbFilter = fvgCandidateStore.verbFilter
  if (display.value === 'all') {
    await fvgCandidateStore.getSentences(segmentationId.value, cursor, undefined, verbFilter)
  } else if (display.value === 'detected' && fvgProcessId.value) {
    await fvgCandidateStore.getDetectedFvgCandidates(fvgProcessId.value, cursor, undefined, verbFilter)
  } else if (display.value === 'undetected' && fvgProcessId.value) {
    await fvgCandidateStore.getUndetectedFvgCandidates(fvgProcessId.value, cursor, undefined, verbFilter)
  }
}

async function goFirst(): Promise<void> {
  if (!allowFirst.value) return
  loading.value = true
  try {
    await fetchPage(null)
    saveCursor(1)
    await scrollToTop()
  } finally {
    loading.value = false
  }
}

async function goPrev(): Promise<void> {
  if (!allowPrev.value || !prevCursor.value) return
  loading.value = true
  try {
    await fetchPage(prevCursor.value)
    saveCursor(Math.max(page.value - 1, 1))
    await scrollToTop()
  } finally {
    loading.value = false
  }
}

async function goNext(): Promise<void> {
  if (!allowNext.value || !nextCursor.value) return
  loading.value = true
  try {
    await fetchPage(nextCursor.value)
    saveCursor(page.value + 1)
    await scrollToTop()
  } finally {
    loading.value = false
  }
}

watch(prevCursor, (prev) => {
  if (!prev && page.value !== 1) saveCursor(1)
})

function onKeydown(e: KeyboardEvent): void {
  if (e.key === 'ArrowLeft') void goPrev()
  else if (e.key === 'ArrowRight') void goNext()
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))

// When display mode changes, restore the last saved cursor for that mode
watch(display, async () => {
  const saved = paginationStore.paginationInfo.fvgSentenceTable[currentMode.value]
  loading.value = true
  try {
    await fetchPage(saved?.currentCursor ?? null)
    if (!saved) {
      saveCursor(1)
    }
    await scrollToTop()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <footer class="bg-violet-200/60 px-4 py-3 text-violet-950 backdrop-blur-md">
    <div class="flex items-center justify-between gap-3">
      <p class="text-sm font-medium">Page {{ page }}</p>
      <div class="flex items-center gap-2">
        <button type="button"
          :disabled="!allowFirst"
          class="cursor-pointer bg-white/45 p-1.5 text-violet-900 transition hover:bg-white/70 disabled:cursor-not-allowed disabled:opacity-40"
          @click="void goFirst()">
          <ChevronFirst class="h-4 w-4" />
        </button>
        <button type="button"
          :disabled="!allowPrev"
          class="cursor-pointer bg-white/45 p-1.5 text-violet-900 transition hover:bg-white/70 disabled:cursor-not-allowed disabled:opacity-40"
          @click="void goPrev()">
          <ChevronLeft class="h-4 w-4" />
        </button>
        <button type="button"
          :disabled="!allowNext"
          class="cursor-pointer bg-violet-500 p-1.5 text-white transition hover:bg-violet-600/85 disabled:cursor-not-allowed disabled:opacity-40"
          @click="void goNext()">
          <ChevronRight class="h-4 w-4" />
        </button>
      </div>
    </div>
  </footer>
</template>