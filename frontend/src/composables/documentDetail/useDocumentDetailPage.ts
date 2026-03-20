import { computed, ref, watch, type Ref } from 'vue'
import { useDocumentStore } from '@/stores/documentStore'
import { useProcessStore } from '@/stores/processStore'
import { useDocumentSourceText } from '@/composables/documentDetail/useDocumentSourceText'
import type { DocumentDetailViewMode } from '@/types/documentDetail'

export function useDocumentDetailPage(docId: Ref<string>) {
  const documentStore = useDocumentStore()
  const processStore = useProcessStore()
  const workspaceLoading = ref(false)

  const documentItem = computed(() => documentStore.getDocumentById(docId.value))
  const processItemsByDocId = computed(() => processStore.getProcessesByDocId(docId.value))
  const segmentationProcess = computed(() => processStore.getSentenceSegmentationProcessByDocId(docId.value))
  const lemmatizeProcess = computed(() => processStore.getLemmatizeProcessBySegmentationId(
    docId.value,
    segmentationProcess.value?.id ?? '',
  ))
  const segmentationRunning = computed(() => processStore.getSegmentationStateByDocId(docId.value))
  const textPath = computed(() => documentItem.value?.textPath ?? '')
  const hasSourceText = computed(() => Boolean(textPath.value.trim()))
  const hasLemmatizeProcess = computed(() => (
    processItemsByDocId.value.some((process) => process.type === 'lemmatize')
  ))
  const canDisplayLemma = computed(() => lemmatizeProcess.value?.state === 'succeed')
  const lemmatizeRunning = computed(() => lemmatizeProcess.value?.state === 'running')
  const lemmatizeFailed = computed(() => lemmatizeProcess.value?.state === 'failed')
  const displayName = computed(() => documentItem.value?.displayName ?? '')
  const formattedCharCount = computed(() => (documentItem.value?.textCharCount ?? 0).toLocaleString())
  const { sourceText, sourceTextLoading } = useDocumentSourceText(textPath)

  const viewMode = computed<DocumentDetailViewMode>(() => {
    if (!documentItem.value) {
      return 'missing'
    }

    if (hasLemmatizeProcess.value) {
      return 'lemma'
    }

    if (processItemsByDocId.value.length > 0) {
      return 'sentence'
    }

    if (hasSourceText.value) {
      return 'source'
    }

    return 'missing'
  })

  async function initializeWorkspace(targetDocId: string): Promise<void> {
    workspaceLoading.value = true

    try {
      const hasDocumentInStore = documentStore.getDocumentById(targetDocId) !== null
      if (!hasDocumentInStore) {
        await documentStore.getAllDocuments()
      }

      await processStore.getAllProcesses()
    } catch {
      // Store actions already preserve error state for rendering.
    } finally {
      workspaceLoading.value = false
    }
  }

  function segmentSentences(): void {
    if (!docId.value) {
      return
    }

    void processStore.segmentDocument(docId.value).catch(() => undefined)
  }

  function startLemmatize(): void {
    if (!docId.value || !segmentationProcess.value || lemmatizeRunning.value) {
      return
    }

    void processStore.lemmatizeSegmentation(docId.value, segmentationProcess.value.id).catch(() => undefined)
  }

  watch(
    docId,
    (nextDocId) => {
      if (!nextDocId) {
        return
      }

      void initializeWorkspace(nextDocId)
    },
    { immediate: true },
  )

  return {
    workspaceLoading,
    documentItem,
    displayName,
    formattedCharCount,
    segmentationProcess,
    canDisplayLemma,
    lemmatizeRunning,
    lemmatizeFailed,
    segmentationRunning,
    sourceText,
    sourceTextLoading,
    viewMode,
    segmentSentences,
    startLemmatize,
  }
}
