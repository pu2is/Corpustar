<script setup lang="ts">
import type { ProcessingItem } from '@/types/processings'

defineProps<{
  processing: ProcessingItem | null
}>()
</script>

<template>
  <section class="rounded border border-border p-3">
    <h3 class="text-sm font-semibold">Processing Status</h3>
    <p
      v-if="!processing"
      class="text-sm text-text-muted"
    >
      No processing yet.
    </p>
    <div
      v-else
      class="text-sm space-y-1"
    >
      <p><strong>id:</strong> {{ processing.id }}</p>
      <p><strong>type:</strong> {{ processing.type }}</p>
      <p><strong>state:</strong> {{ processing.state }}</p>
      <p v-if="processing.errorMessage">
        <strong>error:</strong> {{ processing.errorMessage }}
      </p>
    </div>
  </section>
</template>
