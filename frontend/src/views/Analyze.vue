<script setup lang="ts">
import AnalyzeHeader from '@/components/Analyze/AnalyzeHeader.vue'
</script>

<template>
  <section class="-mx-16 flex h-full flex-col overflow-hidden">
    <AnalyzeHeader />

    <div class="scroll-area min-h-0 flex-1 px-16 ml-16 overflow-y-auto p-6">
      <span>content</span>
    </div>
  </section>
</template>
