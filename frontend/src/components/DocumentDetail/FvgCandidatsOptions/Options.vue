<script setup lang="ts">
import { ref } from 'vue'
import {
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuPortal,
  DropdownMenuRoot,
  DropdownMenuTrigger,
} from 'reka-ui'
import { BarChart2, EllipsisVertical, Trash2 } from 'lucide-vue-next'
import RemoveFvgResultsModal from '@/components/DocumentDetail/FvgCandidatsOptions/RemoveFvgResultsModal.vue'

defineProps<{
  fvgId: string | null
}>()

const removeModalOpen = ref(false)
</script>

<template>
  <RemoveFvgResultsModal v-model:open="removeModalOpen" :fvg-id="fvgId" />

  <DropdownMenuRoot>
    <DropdownMenuTrigger as-child>
      <button type="button"
        class="mt-4 inline-flex cursor-pointer items-center justify-center p-1 outline-none hover:bg-secondary-soft"
        aria-label="Options"
      >
        <EllipsisVertical class="h-4 w-4 shrink-0" />
      </button>
    </DropdownMenuTrigger>

    <DropdownMenuPortal>
      <DropdownMenuContent
        :side-offset="4"
        align="end"
        class="min-w-44 border border-border bg-contrast p-1"
      >
        <DropdownMenuItem
          class="flex cursor-pointer items-center gap-2 px-3 py-2 text-sm text-muted outline-none data-[highlighted]:bg-secondary-soft"
        >
          <BarChart2 class="h-4 w-4 shrink-0" />
          View Statistics
        </DropdownMenuItem>

        <DropdownMenuItem
          class="flex cursor-pointer items-center gap-2 px-3 py-2 text-sm text-red-500 outline-none data-[highlighted]:bg-secondary-soft"
          @select="removeModalOpen = true"
        >
          <Trash2 class="h-4 w-4 shrink-0" />
          Clear FVG Results
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenuPortal>
  </DropdownMenuRoot>
</template>
