import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import App from './App.vue'
import router from './router'
import { connect } from '@/socket/socket'
import { useDocumentStore } from './stores/documentStore'
import { useProcessStore } from './stores/processStore'
import { useSentenceStore } from './stores/sentenceStore'

const pinia = createPinia()
const documentStore = useDocumentStore(pinia)
const processStore = useProcessStore(pinia)
const sentenceStore = useSentenceStore(pinia)
documentStore.bindSocketEvents()
processStore.bindSocketEvents()
sentenceStore.bindSocketEvents()
connect()

createApp(App).use(pinia).use(router).mount('#app')
