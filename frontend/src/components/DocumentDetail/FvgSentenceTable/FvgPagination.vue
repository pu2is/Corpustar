<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { useProcessStore } from '@/stores/processStore'
import { useFvgCandidateStore } from '@/stores/fvgCandidate'
import { getIdFromUrl } from '@/composables/useRouteId'

const docId = getIdFromUrl()
const processStore = useProcessStore()
const fvgCandidateStore = useFvgCandidateStore()

const loading = ref(false)
const page = ref(1)

const segmentationId = computed(() => processStore.getSentenceSegmentationProcessByDocId(docId.value)?.id ?? '')
const fvgProcessId = computed(() => processStore.getFvgProcessByDocId(docId.value)?.id ?? '')
const display = computed(() => fvgCandidateStore.display)
const cursor = computed(() => fvgCandidateStore.cursor)

const prevCursor = computed(() => cursor.value?.previousCursor ?? null)
const nextCursor = computed(() => cursor.value?.nextCursor ?? null)

const allowPrev = computed(() => !loading.value && Boolean(prevCursor.value))
const allowNext = computed(() => !loading.value && Boolean(nextCursor.value))

async function scrollToTop(): Promise<void> {
  await nextTick()
  const el = document.querySelector<HTMLElement>('[data-fvg-sentence-scroll-area]')
  if (el) el.scrollTop = 0
}

async function fetchPage(cursor: string | null): Promise<void> {
  if (!segmentationId.value) return
  if (display.value === 'all') {
    await fvgCandidateStore.getSentences(segmentationId.value, cursor)
  } else if (display.value === 'detected' && fvgProcessId.value) {
    await fvgCandidateStore.getDetectedFvgCandidates(fvgProcessId.value, cursor)
  } else if (display.value === 'undetected' && fvgProcessId.value) {
    await fvgCandidateStore.getUndetectedFvgCandidates(fvgProcessId.value, cursor)
  }
}

async function goPrev(): Promise<void> {
  if (!allowPrev.value || !prevCursor.value) return
  loading.value = true
  try {
    await fetchPage(prevCursor.value)
    page.value = Math.max(page.value - 1, 1)
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
    page.value = page.value + 1
    await scrollToTop()
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <footer class="bg-violet-200/60 px-4 py-3 text-violet-950 backdrop-blur-md">
    <div class="flex items-center justify-between gap-3">
      <p class="text-sm font-medium">Page {{ page }}</p>
      <div class="flex items-center gap-2">
        <button type="button"
          :disabled="!allowPrev"
          class="cursor-pointer bg-white/45 px-3 py-1.5 text-xs font-semibold text-violet-900 transition hover:bg-white/70 disabled:cursor-not-allowed disabled:opacity-40"
          @click="void goPrev()">
          Prev
        </button>
        <button type="button"
          :disabled="!allowNext"
          class="cursor-pointer bg-violet-500 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-violet-600/85 disabled:cursor-not-allowed disabled:opacity-40"
          @click="void goNext()">
          Next
        </button>
      </div>
    </div>
  </footer>
</template>