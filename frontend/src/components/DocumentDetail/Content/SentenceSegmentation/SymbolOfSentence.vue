<script setup lang="ts">
const props = defineProps<{
  value: string
  isLast: boolean
  selected: boolean
}>()

const emit = defineEmits<{
  toggle: []
}>()

function handleToggle(): void {
  if (props.isLast) {
    return
  }
  emit('toggle')
}
</script>

<template>
  <div class="rounded-none px-1 transition-colors duration-150"
    :class="isLast
      ? 'cursor-default'
      : ['cursor-pointer hover:bg-emerald-600 hover:text-emerald-50',
        selected ? 'bg-emerald-700 text-emerald-50' : '']"
    @click="handleToggle">
    {{ value }}
  </div>
</template>
