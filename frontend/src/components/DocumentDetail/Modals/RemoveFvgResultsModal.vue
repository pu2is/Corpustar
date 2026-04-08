<script setup lang="ts">
import { useRouter } from 'vue-router'
import { DialogClose, DialogContent, DialogOverlay, DialogPortal, DialogRoot } from 'reka-ui'
import { useProcessStore } from '@/stores/processStore'
import { APP_ROUTES } from '@/config/routes'

const props = defineProps<{
  fvgId: string | null
}>()

const open = defineModel<boolean>('open', { default: false })

const router = useRouter()
const processStore = useProcessStore()

async function confirmRemove(): Promise<void> {
  if (!props.fvgId) return
  await processStore.deleteFvgResults(props.fvgId)
  open.value = false
  await router.push(APP_ROUTES.documents)
}
</script>

<template>
  <DialogRoot v-model:open="open">
    <DialogPortal>
      <DialogOverlay class="fixed inset-0 z-40 bg-violet-200/40" />
      <DialogContent class="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 bg-violet-700 p-8 shadow-xl focus:outline-none">
        <h2 class="mb-2 text-lg font-semibold text-yellow-300">Clear FVG Results</h2>
        <p class="mb-6 text-sm text-yellow-100/70">
          This will permanently delete all FVG candidates and lemma tokens for this search.
          This action cannot be undone.
        </p>

        <div class="flex items-center justify-end gap-2">
          <DialogClose as-child>
            <button type="button"
              class="cursor-pointer bg-violet-500 px-3 py-1.5 text-sm font-medium text-yellow-300 transition hover:bg-violet-600">
              Cancel
            </button>
          </DialogClose>
          <button type="button"
            :disabled="!fvgId"
            class="cursor-pointer bg-red-500 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-red-600 disabled:cursor-not-allowed disabled:opacity-40"
            @click="confirmRemove()">
            Clear Results
          </button>
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
