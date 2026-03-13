<script setup lang="ts">
defineProps<{
  loading: boolean
  canMerge: boolean
}>()

const emit = defineEmits<{
  segment: []
  merge: []
}>()
</script>

<template>
  <section class="flex gap-2">
    <button
      type="button"
      :disabled="loading"
      class="rounded border px-3 py-1 text-sm disabled:opacity-60"
      @click="emit('segment')"
    >
      Segment Sentences
    </button>
    <button
      type="button"
      :disabled="loading || !canMerge"
      class="rounded border px-3 py-1 text-sm disabled:opacity-60"
      @click="emit('merge')"
    >
      Merge Selected
    </button>
  </section>
</template>
