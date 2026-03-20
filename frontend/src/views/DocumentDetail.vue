<script setup lang="ts">
import DocumentDetailContent from '@/components/DocumentDetail/DocumentDetailContent.vue'
import BackToDocumentsNav from '@/components/DocumentDetail/Header/BackToDocumentsNav.vue'
import DocumentDetailHeader from '@/components/DocumentDetail/Header/DocumentDetailHeader.vue';
import TopNav from '@/components/Nav/TopNav.vue'
</script>

<template>
  <section class="-mx-16 flex h-full flex-col overflow-hidden">
    <header class="relative flex min-h-16 items-center justify-between gap-4 bg-primary px-6 py-4 text-contrast shadow-sm">
      <TopNav />
    </header>
    <!-- Content Header -->
    <div class="min-h-0 flex flex-1 flex-col overflow-hidden px-16 ml-16 p-6">
      <BackToDocumentsNav />
      <DocumentDetailHeader />
      <DocumentDetailContent />
    </div>
  </section>
</template>
