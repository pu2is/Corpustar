<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { getIdFromUrl } from '@/composables/useRouteId'
import { usePaginationStore } from '@/stores/local/paginationStore'
import { useSentenceStore } from '@/stores/sentenceStore'

const docId = getIdFromUrl()
const sentenceStore = useSentenceStore()
const paginationStore = usePaginationStore()

const loading = ref(false)
const page = computed(() => savedCursor.value?.page ?? 1)

const segmentationId = computed(() => sentenceStore.sentenceList.sentences[0]?.version_id ?? '');
const savedCursor = computed(() => paginationStore.paginationInfo.sentenceTable[segmentationId.value])
const prevCursor = computed(() => savedCursor.value?.prevCursor ?? sentenceStore.sentenceList.cursor.prevCursor)
const nextCursor = computed(() => savedCursor.value?.nextCursor ?? sentenceStore.sentenceList.cursor.nextCursor)

const allowPrev = computed(() => !loading.value && Boolean(prevCursor.value))
const allowNext = computed(() => !loading.value && Boolean(nextCursor.value))

async function scrollSentenceListToTop(): Promise<void> {
  await nextTick()
  const scrollArea = document.querySelector<HTMLElement>('[data-sentence-scroll-area]')
  if (scrollArea) {
    scrollArea.scrollTop = 0
  }
}

function saveCursor(page: number): void {
  if (!segmentationId.value) {
    return
  }

  paginationStore.savePagination({
    section: 'sentenceTable',
    cursor: {
      ...paginationStore.paginationInfo.sentenceTable,
      [segmentationId.value]: {
        currentCursor: sentenceStore.sentenceList.cursor.currentCursor,
        prevCursor: sentenceStore.sentenceList.cursor.prevCursor,
        nextCursor: sentenceStore.sentenceList.cursor.nextCursor,
        page,
      },
    },
  })
}

async function goPrev(): Promise<void> {
  if (!docId.value || !segmentationId.value || !prevCursor.value || loading.value) {
    return
  }

  loading.value = true
  try {
    await sentenceStore.getSentences(docId.value, segmentationId.value, prevCursor.value)
    saveCursor(Math.max(page.value - 1, 1))
    await scrollSentenceListToTop()
  } finally {
    loading.value = false
  }
}

async function goNext(): Promise<void> {
  if (!docId.value || !segmentationId.value || !nextCursor.value || loading.value) {
    return
  }

  loading.value = true
  try {
    await sentenceStore.getSentences(docId.value, segmentationId.value, nextCursor.value)
    saveCursor(page.value + 1)
    await scrollSentenceListToTop()
  } finally {
    loading.value = false
  }
}

// Monitor: docId, segmente id changes
watch([docId, segmentationId],
  async ([nextDocId, nextSegmentationId]) => {
    if (!nextDocId || !nextSegmentationId) { return}

    const currentSegmentationId = sentenceStore.sentenceList.sentences[0]?.version_id ?? ''
    const alreadyLoadedCurrentSegmentation = (
      sentenceStore.sentenceList.sentences.length > 0
      && currentSegmentationId === nextSegmentationId
    )

    const saved = paginationStore.paginationInfo.sentenceTable[nextSegmentationId]
    if (!saved || alreadyLoadedCurrentSegmentation) {
      return saveCursor(saved?.page ?? 1)
    }

    loading.value = true
    try {
      await sentenceStore.getSentences(nextDocId, nextSegmentationId, saved.currentCursor)
      saveCursor(saved.page)
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)

// Monitor: sentence table cursor updated (clip & merge)
const cursor = computed(() => sentenceStore.sentenceList.cursor)
watch(cursor, () => {
  if (!segmentationId.value) { return }
  saveCursor(page.value)
},{ deep: true })

watch([prevCursor, page], ([nextPrevCursor, nextPage]) => {
  if (!segmentationId.value) { return }
  if (!nextPrevCursor && nextPage !== 1) {
    saveCursor(1)
  }
}, { immediate: true })
</script>

<template>
  <footer class="bg-violet-200/60 px-4 py-3 text-violet-950 backdrop-blur-md">
    <div class="flex items-center justify-between gap-3">
      <p class="text-sm font-medium">
        Page {{ page }}
      </p>
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
