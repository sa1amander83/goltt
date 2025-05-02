import './assets/css/main.css'

import { createApp } from 'vue'
import { createBootstrap } from 'bootstrap-vue-next'
import { createPinia } from 'pinia'
import store from './stores/index'
import App from './App.vue'
import router from './router'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue-next/dist/bootstrap-vue-next.css'
import '@fortawesome/fontawesome-free/css/all.css'
const app = createApp(App)
app.use(store)
app.use(createPinia())
app.use(router)
app.use(createBootstrap())
app.mount('#app')
