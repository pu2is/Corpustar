import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import App from './App.vue'
import router from './router'
import { connect } from '@/socket/socket'
import { useDocumentStore } from './stores/documentStore'
import { useProcessStore } from './stores/processStore'
import { useRuleStore } from './stores/ruleStore'
import { useRuleFvgStore } from './stores/ruleFvgStore'
import { useSentenceStore } from './stores/sentenceStore'
import { usePaginationStore } from './stores/local/paginationStore'
import { useFvgCandidateStore } from './stores/fvgCandidate'

const pinia = createPinia()
const documentStore = useDocumentStore(pinia)
const processStore = useProcessStore(pinia)
const ruleStore = useRuleStore(pinia)
const ruleFvgStore = useRuleFvgStore(pinia)
const sentenceStore = useSentenceStore(pinia)
const paginationStore = usePaginationStore(pinia)
const fvgCandidateStore = useFvgCandidateStore(pinia)
documentStore.bindSocketEvents()
processStore.bindSocketEvents()
ruleStore.bindSocketEvents()
ruleFvgStore.bindSocketEvents()
sentenceStore.bindSocketEvents()
fvgCandidateStore.bindSocketEvents()
paginationStore.loadPagination()
connect()

createApp(App).use(pinia).use(router).mount('#app')
