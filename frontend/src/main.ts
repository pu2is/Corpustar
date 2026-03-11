import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import App from './App.vue'
import router from './router'
import { connectGlobalSocket } from './socket/globalSocket'
import { useDocumentStore } from './stores/documentStore'

const pinia = createPinia()
const documentStore = useDocumentStore(pinia)

connectGlobalSocket(documentStore)

createApp(App).use(pinia).use(router).mount('#app')
