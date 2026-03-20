<script setup lang="ts">
const props = defineProps<{
  running: boolean
  failed: boolean
}>()

const emit = defineEmits<{
  lemmatize: []
}>()
</script>

<template>
  <button type="button" :disabled="props.running"
    class="cursor-pointer rounded-[2px] bg-amber-400 px-4 py-1 text-lg font-medium text-violet-500 transition hover:bg-amber-400/85 disabled:cursor-not-allowed disabled:opacity-60"
    @click="emit('lemmatize')">
    <span class="relative inline-block">
      <span aria-hidden="true"
        class="absolute bottom-[1px] left-[1px] w-full whitespace-nowrap text-cyan-300">
        {{ props.running ? 'Lemmatizing...' : (props.failed ? 'Retry Lemmatize' : 'Start Lemmatize') }}
      </span>
      <span class="relative whitespace-nowrap">
        {{ props.running ? 'Lemmatizing...' : (props.failed ? 'Retry Lemmatize' : 'Start Lemmatize') }}
      </span>
    </span>
  </button>
</template>
