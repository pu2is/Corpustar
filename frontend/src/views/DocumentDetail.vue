<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ChevronLeft } from 'lucide-vue-next'
import { storeToRefs } from 'pinia'
import { useRoute, useRouter } from 'vue-router'
// components
import TopNav from '@/components/Nav/TopNav.vue'
import { useDocumentStore } from '@/stores/documentStore'

const route = useRoute()
const router = useRouter()
const documentStore = useDocumentStore()
const { documents, loading } = storeToRefs(documentStore)

const docId = computed(() => {
  const value = route.params.doc_id
  return typeof value === 'string' ? value : ''
})

const documentItem = computed(() => documents.value.find((doc) => doc.id === docId.value) ?? null)
const documentText = ref('')
const textLoading = ref(false)
const textError = ref<string | null>(null)

async function loadDocumentText(): Promise<void> {
  const item = documentItem.value
  if (!item) {
    documentText.value = ''
    textError.value = null
    return
  }

  if (!item.textPath) {
    documentText.value = ''
    textError.value = 'No text file path found for this document.'
    return
  }

  if (!window.electronAPI?.readDocumentText) {
    documentText.value = ''
    textError.value = 'Electron text reader unavailable. Start with npm run electron:dev.'
    return
  }

  textLoading.value = true
  textError.value = null
  try {
    documentText.value = await window.electronAPI.readDocumentText(item.textPath)
  } catch (error) {
    documentText.value = ''
    textError.value = error instanceof Error ? error.message : String(error)
  } finally {
    textLoading.value = false
  }
}

onMounted(() => {
  if (!documents.value.length && !loading.value) {
    void documentStore.getAllDocuments()
  }
})

watch(() => documentItem.value?.textPath ?? '', () => {
  void loadDocumentText()
}, { immediate: true })

function backToDocuments(): void {
  void router.push('/analyze')
}
</script>

<template>
  <section class="-mx-16 flex h-full flex-col overflow-hidden">
    <header class="relative flex min-h-16 items-center justify-between gap-4 bg-primary px-6 py-4 text-contrast shadow-sm">
      <TopNav />
    </header>

    <!-- Content Header -->
    <div class="scroll-area min-h-0 flex-1 px-16 ml-16 overflow-y-auto p-6">
      <button type="button"
        class="mb-4 cursor-pointer inline-flex items-center gap-2 text-sm font-medium text-text-muted transition-colors hover:text-text"
        @click="backToDocuments">
        <ChevronLeft class="h-4 w-4" />
        Back to documents
      </button>

      <!-- Content Body -->
      <section v-if="loading && !documentItem"
        class="text-sm text-text-muted">
        Loading document...
      </section>

      <section v-else-if="documentItem"
        class="space-y-3">
        <header>
          <h2 class="text-xl font-semibold text-text">
            {{ documentItem.displayName }}
          </h2>
          <p class="text-sm text-text-muted">
            {{ documentItem.filename }}
          </p>
        </header>
        <section class="overflow-hidden rounded border border-border bg-background-elevated/40">
          <p v-if="textLoading"
            class="px-4 py-3 text-sm text-text-muted">
            Loading text...
          </p>
          <p v-else-if="textError"
            class="px-4 py-3 text-sm text-error">
            {{ textError }}
          </p>
          <pre v-else
            class="max-h-[60vh] overflow-auto whitespace-pre-wrap break-words px-4 py-3 text-sm leading-6 text-text">{{ documentText || 'No text content available.' }}</pre>
        </section>
      </section>

      <section v-else
        class="text-sm text-text-muted">
        Document with id "{{ docId }}" was not found.
      </section>
    </div>
  </section>
</template>
