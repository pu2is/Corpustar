import { createRouter, createWebHashHistory } from 'vue-router'

import AnalyzeView from '@/views/Documents.vue'
import DocumentDetailView from '@/views/DocumentDetail.vue'
import RulesView from '@/views/Rules.vue'
import RuleDetailView from '@/views/RuleDetail.vue'
import { APP_ROUTES } from '@/config/routes'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: APP_ROUTES.root,
      redirect: APP_ROUTES.documents,
    },
    {
      path: APP_ROUTES.rules,
      component: RulesView,
      meta: {
        title: 'Rules',
        caption: 'Operational guardrails, intake standards, and review policy.',
      },
    },
    {
      path: `${APP_ROUTES.rules}/:id`,
      component: RuleDetailView,
      meta: {
        title: 'Rule Table',
        caption: 'Rule table in detail.',
      },
    },
    {
      path: APP_ROUTES.documents,
      component: AnalyzeView,
      meta: {
        title: 'Analyze',
        caption: 'Review the analysis lane before decisions are published.',
      },
    },
    {
      path: `${APP_ROUTES.documents}/:id`,
      component: DocumentDetailView,
      meta: {
        title: 'Document Detail',
        caption: 'Inspect one document and then return to documents list.',
      },
    },
  ],
})

export default router
