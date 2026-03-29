<script setup lang="ts">
import type { LemmaViewItem } from '@/types/lemmatize'

const props = defineProps<{
  item: LemmaViewItem
}>()
</script>

<template>
  <article class="grid gap-3S md:grid-cols-2">
    <section class="space-y-2 bg-violet-100 px-4 py-3">
      <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-violet-500/80">
        Source Text
      </p>
      <p class="break-words text-sm font-medium text-violet-700">
        {{ props.item.source_text }}
      </p>
    </section>

    <section class="space-y-2 border border-violet-500 bg-background px-4 py-3">
      <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-muted">
        Lemma Text
      </p>
      <p class="break-words text-sm text-violet-950">
        {{ props.item.lemma_text }}
      </p>
    </section>
  </article>
</template>
