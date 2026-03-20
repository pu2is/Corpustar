<script setup lang="ts">
import { ChevronLeft } from 'lucide-vue-next'

const emit = defineEmits<{
  back: []
}>()
</script>

<template>
  <button type="button"
    class="mb-4 inline-flex shrink-0 cursor-pointer items-center gap-2 text-sm font-medium text-text-muted transition-colors hover:text-violet-950"
    @click="emit('back')">
    <ChevronLeft class="h-4 w-4" />
    Back to documents
  </button>
</template>
