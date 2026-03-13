<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  close: []
  submit: [splitOffset: number]
}>()

const splitOffsetInput = ref('')

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      splitOffsetInput.value = ''
    }
  },
)

function submit(): void {
  const splitOffset = Number.parseInt(splitOffsetInput.value, 10)
  if (!Number.isFinite(splitOffset)) {
    return
  }
  emit('submit', splitOffset)
}
</script>

<template>
  <div
    v-if="open"
    class="mt-2 rounded border p-2 space-y-2"
  >
    <label class="block text-sm">
      Split Offset
      <input
        v-model="splitOffsetInput"
        type="number"
        class="mt-1 w-full rounded border px-2 py-1 text-sm"
      >
    </label>
    <div class="flex gap-2">
      <button
        type="button"
        class="rounded border px-2 py-1 text-sm"
        @click="submit"
      >
        Apply
      </button>
      <button
        type="button"
        class="rounded border px-2 py-1 text-sm"
        @click="emit('close')"
      >
        Cancel
      </button>
    </div>
  </div>
</template>
