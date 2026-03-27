<script setup lang="ts">
import DocumentsHeader from '@/components/Documents/DocumentsHeader.vue'
import DocumentTable from '@/components/Documents/Content/DocumentTable.vue';
</script>

<template>
  <section class="-mx-16 flex h-full flex-col overflow-hidden">
    <DocumentsHeader />

    <div class="min-h-0 flex flex-1 flex-col overflow-hidden px-16 ml-16 p-6">
      <DocumentTable class="min-h-0 flex-1" />
    </div>
  </section>
</template>
