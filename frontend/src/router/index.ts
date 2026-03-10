import { createRouter, createWebHashHistory } from 'vue-router'

import AnalyzeView from '../views/Analyze.vue'
import RulesView from '../views/Rules.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      redirect: '/analyze',
    },
    {
      path: '/rules',
      component: RulesView,
      meta: {
        title: 'Rules',
        caption: 'Operational guardrails, intake standards, and review policy.',
      },
    },
    {
      path: '/analyze',
      component: AnalyzeView,
      meta: {
        title: 'Analyze',
        caption: 'Review the analysis lane before decisions are published.',
      },
    },
  ],
})

export default router
