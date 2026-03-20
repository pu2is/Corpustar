<script setup lang="ts">
import { BookOpenText } from 'lucide-vue-next'
import WorkflowControl from '@/components/DocumentDetail/Header/WorkflowControl.vue'

const props = defineProps<{
  displayName: string
  formattedCharCount: string
  showWorkflowControl: boolean
  lemmatizeRunning: boolean
  lemmatizeFailed: boolean
}>()

const emit = defineEmits<{
  lemmatize: []
}>()
</script>

<template>
  <header class="space-y-1 py-3">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h2 class="text-xl font-semibold text-violet-950">
        {{ props.displayName }}
      </h2>

      <WorkflowControl
        v-if="props.showWorkflowControl"
        :running="props.lemmatizeRunning"
        :failed="props.lemmatizeFailed"
        @lemmatize="emit('lemmatize')" />
    </div>

    <p class="inline-flex items-center gap-2 bg-cyan-300 px-2 py-1 text-sm text-cyan-800">
      <BookOpenText class="h-3.5 w-3.5" />
      {{ props.formattedCharCount }} characters
    </p>
  </header>
</template>
