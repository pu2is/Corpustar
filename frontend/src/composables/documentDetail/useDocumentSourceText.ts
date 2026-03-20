import { ref, watch, type Ref } from 'vue'

export function useDocumentSourceText(textPath: Ref<string>) {
  const sourceText = ref('')
  const sourceTextLoading = ref(false)
  let textRequestId = 0

  async function loadSourceText(nextTextPath: string): Promise<void> {
    const requestId = ++textRequestId
    sourceTextLoading.value = true

    try {
      if (!window.electronAPI?.readDocumentText) {
        throw new Error('Document text reader unavailable. Restart is required.')
      }

      const content = await window.electronAPI.readDocumentText(nextTextPath)
      if (requestId === textRequestId) {
        sourceText.value = content
      }
    } catch {
      if (requestId === textRequestId) {
        sourceText.value = ''
      }
    } finally {
      if (requestId === textRequestId) {
        sourceTextLoading.value = false
      }
    }
  }

  watch(
    textPath,
    (nextTextPath) => {
      if (!nextTextPath) {
        textRequestId += 1
        sourceText.value = ''
        sourceTextLoading.value = false
        return
      }

      void loadSourceText(nextTextPath)
    },
    { immediate: true },
  )

  return {
    sourceText,
    sourceTextLoading,
  }
}
