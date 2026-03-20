<script setup lang="ts">
const props = defineProps<{
  currentPage: number
  itemCount: number
  hasPrevious: boolean
  hasNext: boolean
  loading: boolean
}>()

const emit = defineEmits<{
  previous: []
  next: []
}>()
</script>

<template>
  <footer class="bg-violet-200/60 px-4 py-3 text-violet-950 shadow-[0_16px_36px_-24px_rgba(109,40,217,0.9)] backdrop-blur-md">
    <div class="flex items-center justify-between gap-3">
      <div class="min-w-0">
        <p class="truncate text-sm font-medium">
          Page {{ props.currentPage }}
        </p>
      </div>

      <div class="flex items-center gap-2">
        <button type="button"
          :disabled="props.loading || !props.hasPrevious"
          class="cursor-pointer bg-white/45 px-3 py-1.5 text-xs font-semibold text-violet-900 transition hover:bg-white/70 disabled:cursor-not-allowed disabled:opacity-45"
          @click="emit('previous')">
          Prev
        </button>
        <button type="button" :disabled="props.loading || !props.hasNext"
          class="cursor-pointer bg-violet-500 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-violet-600/85 disabled:cursor-not-allowed disabled:opacity-45"
          @click="emit('next')">
          Next
        </button>
      </div>
    </div>
  </footer>
</template>
