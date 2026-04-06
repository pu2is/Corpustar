<script setup lang="ts">
import { computed } from 'vue';
import { ChevronDown, Check } from 'lucide-vue-next';
import { DropdownMenuContent, DropdownMenuItem,
  DropdownMenuPortal, DropdownMenuRoot, DropdownMenuTrigger } from 'reka-ui';
import { useFvgCandidateStore } from '@/stores/fvgCandidate';

const fvgCandidateStore = useFvgCandidateStore();

const displayOptions: { value: 'detected' | 'undetected' | 'all'; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'detected', label: 'Matched' },
  { value: 'undetected', label: 'Unmatched'},
];

const fvgSentenceTableDisplay = computed(() => fvgCandidateStore.display);
const fvgDisplayLabel = computed(() => displayOptions.find(o => o.value === fvgSentenceTableDisplay.value)?.label ?? '');

function changeFvgSentenceTableDisplay(display: 'detected' | 'undetected' | 'all'): void {
  fvgCandidateStore.changeDisplay(display);
}
</script>

<template>
  <DropdownMenuRoot>
    <div class="flex flex-col items-end gap-0.5">
      <span class="text-[10px] uppercase tracking-widest text-muted">View</span>
      <DropdownMenuTrigger as-child>
        <button type="button"
          class="inline-flex w-28 cursor-pointer items-center justify-between gap-1.5 border border-violet-400 px-2.5 py-1 text-xs text-violet-600 outline-none transition hover:border-violet-600 hover:text-violet-700">
          {{ fvgDisplayLabel }}
          <ChevronDown class="h-3 w-3 shrink-0" />
        </button>
      </DropdownMenuTrigger>
    </div>

    <DropdownMenuPortal>
      <DropdownMenuContent :side-offset="4" align="end"
        class="w-28 border border-border bg-contrast p-0.5 shadow-md">
        <DropdownMenuItem
          v-for="option in displayOptions"
          :key="option.value"
          class="flex w-full cursor-pointer items-center justify-between px-2.5 py-1.5 text-xs outline-none data-[highlighted]:bg-secondary-soft"
          :class="fvgSentenceTableDisplay === option.value ? 'text-violet-600' : 'text-muted'"
          @select="changeFvgSentenceTableDisplay(option.value)">
          {{ option.label }}
          <Check v-if="fvgSentenceTableDisplay === option.value" class="h-3 w-3 shrink-0" />
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenuPortal>
  </DropdownMenuRoot>
</template>