<script setup lang="ts">
defineProps<{
  value: string
  isLast: boolean
}>()
</script>

<template>
  <div class="rounded-none px-1 transition-colors duration-150"
    :class="isLast
      ? 'cursor-default'
      : 'hover:bg-sky-600 hover:text-sky-100'">
    {{ value }}
  </div>
</template>
