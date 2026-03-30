<script setup lang="ts">
// types
import type { DocItem } from '@/types/documents';
// icons
import { BookOpenText } from 'lucide-vue-next';

const props = defineProps<{
  document: DocItem;
}>();
</script>

<template>
  <header class="space-y-1 py-3">
    <h2 class="text-xl font-semibold text-violet-950">
      {{ document.display_name }}
    </h2>
    <p class="inline-flex items-center gap-2 text-sm text-violet-500">
      <BookOpenText class="h-3.5 w-3.5" />
      {{ document.char_count }} characters
    </p>
  </header>
</template>