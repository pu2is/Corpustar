<template>
  <div class="relative h-screen w-screen bg-surface text-contrast-strong">
    <SideNav />
    <main class="h-full w-full overflow-auto px-16 py-4">
      <RouterView v-slot="{ Component, route }">
        <Transition mode="out-in"
          enter-active-class="transition-opacity duration-400 ease-out"
          enter-from-class="opacity-30"
          enter-to-class="opacity-100"
          leave-active-class="transition-opacity duration-400 ease-in"
          leave-from-class="opacity-100"
          leave-to-class="opacity-30" >
          <component :is="Component" :key="route.fullPath" />
        </Transition>
      </RouterView>
    </main>
  </div>
</template>

<script setup lang="ts">
import SideNav from '@/components/Nav/SideNav.vue'
</script>
