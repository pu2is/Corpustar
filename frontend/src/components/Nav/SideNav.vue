<script setup lang="ts">
import { PencilRuler, TextSearch } from 'lucide-vue-next'
import { NavigationMenuItem, NavigationMenuLink, NavigationMenuList, NavigationMenuRoot } from 'reka-ui'
import { useRoute } from 'vue-router'

const route = useRoute()

const links = [
  { label: 'Analyze', to: '/analyze', icon: TextSearch },
  { label: 'Rules', to: '/rules', icon: PencilRuler },
]

function isActive(path: string): boolean {
  return route.path === path
}

const navLinkBaseClass =
  'group inline-flex h-11 w-fit items-center justify-start overflow-hidden px-3 text-sm font-medium transition-[background-color,color,box-shadow] duration-300 ease-out'

const navLabelClass =
  'ml-0 max-w-0 overflow-hidden whitespace-nowrap -translate-x-1 opacity-0 transition-[max-width,margin,opacity,transform] duration-300 ease-out group-hover:ml-2 group-hover:max-w-40 group-hover:translate-x-0 group-hover:opacity-100 group-focus-visible:ml-2 group-focus-visible:max-w-40 group-focus-visible:translate-x-0 group-focus-visible:opacity-100'

function navLinkStateClass(active: boolean): string {
  if (active) {
    return 'bg-primary !text-contrast shadow-sm hover:bg-primary-hover'
  }

  return 'bg-secondary-soft text-contrast-strong hover:bg-secondary hover:text-contrast'
}
</script>

<template>
  <aside class="absolute left-4 top-1/2 z-10 -translate-y-1/2">
    <NavigationMenuRoot orientation="vertical" class="flex items-center">
      <NavigationMenuList class="flex flex-col items-start gap-2">
        <NavigationMenuItem v-for="item in links" :key="item.to">
          <NavigationMenuLink as-child>
            <RouterLink :to="item.to"
              :class="[navLinkBaseClass, navLinkStateClass(isActive(item.to))]">
              <component :is="item.icon" class="h-4 w-4 shrink-0" />
              <span :class="navLabelClass">
                {{ item.label }}
              </span>
            </RouterLink>
          </NavigationMenuLink>
        </NavigationMenuItem>
      </NavigationMenuList>
    </NavigationMenuRoot>
  </aside>
</template>
