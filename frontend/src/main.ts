import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import App from './App.vue'
import router from './router'
import { connect } from '@/socket/socket'
import { useDocumentStore } from './stores/documentStore'

const pinia = createPinia()
const documentStore = useDocumentStore(pinia)
documentStore.bindSocketEvents()
connect()

createApp(App).use(pinia).use(router).mount('#app')
