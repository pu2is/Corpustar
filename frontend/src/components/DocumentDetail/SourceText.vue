<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import type { DocItem } from '@/types';

const props = defineProps<{
  documents: DocItem
}>();

const textPath = computed(() => props.documents.text_path);

const text = ref('');
const textLoading = ref(false);

async function loadText(nextTextPath: string): Promise<void> {
  textLoading.value = true;
  try {
    if (!window.electronAPI?.readDocumentText) {
      throw new Error('Document text reader unavailable. Restart is required.');
    }
    text.value = await window.electronAPI.readDocumentText(nextTextPath);
  } catch {
    text.value = '';
  } finally {
    textLoading.value = false;
  }
}

watch(textPath,
  (nextTextPath) => {
    if (!nextTextPath) {
      text.value = '';
      textLoading.value = false;
      return;
    }

    void loadText(nextTextPath);
  },
  { immediate: true },
);

</script>

<template>
  <section class="min-h-0 flex flex-1 flex-col overflow-hidden rounded border border-border/60 bg-background-elevated/25 p-3">
    <p v-if="textLoading" class="text-sm text-text-muted">
      Loading source text...
    </p>
    <div v-else class="scroll-area min-h-0 flex-1 overflow-y-auto whitespace-pre-wrap break-words pr-1 text-sm text-violet-950">
      {{ text || 'No source text available.' }}
    </div>
  </section>
</template>
