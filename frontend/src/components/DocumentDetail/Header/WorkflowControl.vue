<script setup lang="ts">
import {AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription,
  AlertDialogOverlay, AlertDialogPortal, AlertDialogRoot, AlertDialogTitle, AlertDialogTrigger} from 'reka-ui'

const props = defineProps<{
  running: boolean
  failed: boolean
}>()

const emit = defineEmits<{
  lemmatize: []
}>()

function handleStart(): void {
  if (props.running) {
    return
  }

  emit('lemmatize')
}
</script>

<template>
  <AlertDialogRoot>
    <AlertDialogTrigger as-child>
      <button
        type="button"
        :disabled="props.running"
        class="cursor-pointer rounded-none bg-amber-400 px-4 py-1 text-lg font-medium text-violet-500 transition hover:bg-amber-400/85 disabled:cursor-not-allowed disabled:opacity-60">
        <span class="relative inline-block">
          <span
            aria-hidden="true"
            class="absolute bottom-[1px] left-[1px] w-full whitespace-nowrap text-cyan-300">
            {{ props.running ? 'Lemmatizing...' : (props.failed ? 'Retry Lemmatize' : 'Start Lemmatize') }}
          </span>
          <span class="relative whitespace-nowrap">
            {{ props.running ? 'Lemmatizing...' : (props.failed ? 'Retry Lemmatize' : 'Start Lemmatize') }}
          </span>
        </span>
      </button>
    </AlertDialogTrigger>

    <AlertDialogPortal>
      <AlertDialogOverlay class="fixed inset-0 z-40 bg-violet-950/35 backdrop-blur-[2px]" />

      <AlertDialogContent
        class="fixed left-1/2 top-1/2 z-50 w-[min(92vw,32rem)] -translate-x-1/2 -translate-y-1/2 rounded-none bg-yellow-300 p-6 text-violet-700 shadow-[0_24px_80px_-28px_rgba(76,29,149,0.9)] focus:outline-none">
        <div class="space-y-5">
          <div class="space-y-2">
            <AlertDialogTitle class="text-xl font-semibold uppercase tracking-[0.06em]">
              Start Lemmatization
            </AlertDialogTitle>

            <AlertDialogDescription class="text-sm leading-6 text-violet-700/90">
              Please confirm that all sentences have been segmented correctly and reviewed before starting
              lemmatization.
            </AlertDialogDescription>
          </div>

          <div class="flex justify-end gap-3">
            <AlertDialogCancel as-child>
              <button
                type="button"
                class="cursor-pointer rounded-none border border-violet-700 px-4 py-2 text-sm font-semibold text-violet-700 transition hover:bg-violet-700/10">
                Close
              </button>
            </AlertDialogCancel>

            <AlertDialogAction as-child>
              <button
                type="button"
                class="cursor-pointer rounded-none bg-violet-500 px-4 py-2 text-sm font-semibold text-yellow-300 transition hover:bg-violet-600 disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="props.running"
                @click="handleStart">
                Start
              </button>
            </AlertDialogAction>
          </div>
        </div>
      </AlertDialogContent>
    </AlertDialogPortal>
  </AlertDialogRoot>
</template>
