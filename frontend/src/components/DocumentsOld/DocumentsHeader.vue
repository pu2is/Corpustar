<script setup lang="ts">
import AddText from '@/components/DocumentsOld/Header/AddText.vue'
import TopNav from '@/components/Nav/TopNav.vue'
</script>

<template>
  <header class="relative flex min-h-16 items-center justify-between gap-4 bg-primary px-6 py-4 text-contrast shadow-sm">
    <TopNav />
    <AddText />
  </header>
</template>
