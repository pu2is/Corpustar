<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DocumentDetailContent from '@/components/DocumentDetail/DocumentDetailContent.vue'
import BackToDocumentsNav from '@/components/DocumentDetail/Header/BackToDocumentsNav.vue'
import DocumentDetailHeader from '@/components/DocumentDetail/Header/DocumentDetailHeader.vue'
import TopNav from '@/components/Nav/TopNav.vue'
import { useDocumentDetailPage } from '@/composables/documentDetail/useDocumentDetailPage'

const route = useRoute()
const router = useRouter()

const docId = computed(() => {
  const param = route.params.doc_id
  return Array.isArray(param) ? (param[0] ?? '') : (param ?? '')
})

const {
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
  workspaceLoading,
  segmentSentences,
  startLemmatize,
} = useDocumentDetailPage(docId)

function backToDocuments(): void {
  void router.push('/analyze')
}
</script>

<template>
  <main class="-mx-16 flex h-full flex-col overflow-hidden">
    <header class="relative flex min-h-16 items-center justify-between gap-4 bg-primary px-6 py-4 text-contrast shadow-sm">
      <TopNav />
    </header>

    <section class="ml-16 min-h-0 flex flex-1 flex-col overflow-hidden p-6 px-16">
      <BackToDocumentsNav @back="backToDocuments" />

      <DocumentDetailHeader
        :display-name="displayName"
        :formatted-char-count="formattedCharCount"
        :show-workflow-control="Boolean(segmentationProcess && !canDisplayLemma)"
        :lemmatize-running="lemmatizeRunning"
        :lemmatize-failed="lemmatizeFailed"
        @lemmatize="startLemmatize" />

      <DocumentDetailContent
        :doc-id="docId"
        :workspace-loading="workspaceLoading"
        :view-mode="viewMode"
        :source-text="sourceText"
        :source-text-loading="sourceTextLoading"
        :segmentation-running="segmentationRunning"
        @segment="segmentSentences" />
    </section>
  </main>
</template>
