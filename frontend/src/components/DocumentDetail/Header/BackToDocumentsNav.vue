<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ChevronLeft } from 'lucide-vue-next'

const router = useRouter()

function backToDocuments(): void {
  void router.push('/analyze')
}
</script>

<template>
  <button type="button"
    class="mb-4 inline-flex shrink-0 cursor-pointer items-center gap-2 text-sm font-medium text-text-muted transition-colors hover:text-text"
    @click="backToDocuments">
    <ChevronLeft class="h-4 w-4" />
    Back to documents
  </button>
</template>
