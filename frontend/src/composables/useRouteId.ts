import { computed } from 'vue'
import { useRoute } from 'vue-router'

type RouteParamValue = string | string[] | undefined

export function getIdFromUrl() {
  const route = useRoute()

  return computed(() => {
    const param = route.params.id as RouteParamValue
    if (Array.isArray(param)) {
      return param[0] || ''
    }
    return param || ''
  })
}
