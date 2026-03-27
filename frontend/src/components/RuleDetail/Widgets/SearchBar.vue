<script setup lang="ts">
import { Delete } from 'lucide-vue-next'

const props = defineProps<{
  modelValue: string
  matches: number
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

function updateValue(event: Event): void {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}

function clearSearch(): void {
  emit('update:modelValue', '')
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    clearSearch()
  }
}
</script>

<template>
  <header class="shrink-0 flex items-center gap-2 bg-background-elevated px-3 py-4">
    <div class="relative flex-1">
      <input type="text"
        :value="props.modelValue"
        placeholder="Search verb or phrase..."
        class="h-9 w-full border border-secondary/20 bg-background px-3 pr-10 text-sm text-violet-950 outline-none transition-colors placeholder:text-text-muted/70 focus:border-secondary/50"
        @input="updateValue"
        @keydown="handleKeydown">
      <button v-if="props.modelValue"
        type="button"
        class="absolute right-1 top-1/2 inline-flex h-7 w-7 -translate-y-1/2 cursor-pointer items-center justify-center rounded text-text-muted transition-colors hover:bg-secondary/10 hover:text-violet-950"
        aria-label="Clear search"
        @click="clearSearch">
        <Delete class="h-4 w-4" />
      </button>
    </div>
    <span class="inline-block w-[15ch] shrink-0 text-right text-xs tabular-nums text-text-muted">
      {{ props.matches }} match{{ props.matches === 1 ? '' : 'es' }}
    </span>
  </header>
</template>
