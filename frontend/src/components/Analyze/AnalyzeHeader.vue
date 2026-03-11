<script setup lang="ts">
import AddText from '@/components/Analyze/Header/AddText.vue'
import TopNav from '@/components/Nav/TopNav.vue'

const emit = defineEmits<{
  (e: 'file-selected', file: File): void
}>()

function handleFileSelected(file: File): void {
  emit('file-selected', file)
}
</script>

<template>
  <header class="relative flex min-h-16 items-center justify-between gap-4 bg-primary px-6 py-4 text-contrast shadow-sm">
    <TopNav />
    <AddText @file-selected="handleFileSelected" />
  </header>
</template>
