<script setup lang="ts">
import { nextTick, ref } from 'vue'

import type { SentenceItem } from '@/types/sentences'

const props = defineProps<{
  item: SentenceItem
  loading: boolean
  canMergePrev: boolean
  highlighted: boolean
}>()

const emit = defineEmits<{
  requestMerge: [sentenceId: string]
  clip: [sentenceId: string, splitOffset: number]
}>()

const clipInputMode = ref(false)
const clipInputRef = ref<HTMLTextAreaElement | null>(null)
const sanitizeInputEnabled = ref(false)

function requestMergePrev(): void {
  emit('requestMerge', props.item.id)
}

function openClipInput(): void {
  sanitizeInputEnabled.value = true
  clipInputMode.value = true
  void nextTick(() => {
    const input = clipInputRef.value
    if (!input) {
      return
    }
    input.focus()
    const cursorIndex = props.item.text.length
    input.setSelectionRange(cursorIndex, cursorIndex)
  })
}

function closeClipInput(): void {
  sanitizeInputEnabled.value = false
  clipInputMode.value = false
}

function submitClipAtCursor(): void {
  const input = clipInputRef.value
  if (!input) {
    return
  }
  const cursorIndex = input.selectionStart ?? 0
  if (cursorIndex >= props.item.text.length) {
    closeClipInput()
    return
  }

  const splitOffset = props.item.startOffset + cursorIndex
  if (splitOffset <= props.item.startOffset || splitOffset >= props.item.endOffset) {
    return
  }

  emit('clip', props.item.id, splitOffset)
  sanitizeInputEnabled.value = false
  clipInputMode.value = false
}

function handleClipInputKeydown(event: KeyboardEvent): void {
  if (event.key === 'Enter') {
    event.preventDefault()
    submitClipAtCursor()
    return
  }

  if (event.key === 'Escape') {
    event.preventDefault()
    closeClipInput()
  }
}

function preventTextMutation(event: InputEvent): void {
  event.preventDefault()
}

function sanitizeInput(event: Event): void {
  if (!sanitizeInputEnabled.value) {
    return
  }

  const target = event.target
  if (!(target instanceof HTMLTextAreaElement)) {
    return
  }

  const cursorStart = target.selectionStart ?? 0
  const cursorEnd = target.selectionEnd ?? cursorStart
  target.value = props.item.text
  const maxCursor = props.item.text.length
  target.setSelectionRange(
    Math.min(cursorStart, maxCursor),
    Math.min(cursorEnd, maxCursor),
  )
}

function handleClipClick(): void {
  if (clipInputMode.value) {
    closeClipInput()
    return
  }
  openClipInput()
}
</script>

<template>
  <div class="rounded border p-2 space-y-2 transition-colors duration-200"
    :class="highlighted ? 'border-emerald-500 bg-emerald-50/60' : 'border-border'">
    <div class="flex items-start gap-2">
      <div class="min-w-0 flex-1 space-y-1">
        <p class="text-xs text-text-muted">
          {{ item.startOffset }} - {{ item.endOffset }}
        </p>
        <p v-if="!clipInputMode"
          class="text-sm whitespace-pre-wrap break-words">
          {{ item.text }}
        </p>
        <textarea v-else
          ref="clipInputRef"
          :value="item.text"
          class="w-full rounded border px-2 py-1 text-sm caret-current"
          rows="3"
          @keydown="handleClipInputKeydown"
          @input="sanitizeInput"
          @beforeinput="preventTextMutation"
          @paste.prevent
          @drop.prevent
          @cut.prevent />
      </div>
    </div>
    <div class="flex gap-2">
      <button type="button"
        :disabled="loading || !canMergePrev"
        class="rounded border px-2 py-1 text-xs disabled:opacity-60"
        @click="requestMergePrev">
        Merge Prev
      </button>
      <button type="button"
        :disabled="loading"
        class="rounded border px-2 py-1 text-xs disabled:opacity-60"
        @click="handleClipClick">
        {{ clipInputMode ? 'Cancel Clip' : 'Clip' }}
      </button>
    </div>
  </div>
</template>
