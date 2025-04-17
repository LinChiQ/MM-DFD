import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'
import './assets/css/global.css'
import axios from 'axios'

// 提供默认logo
import DefaultLogo from './assets/logo.svg'
Vue.prototype.$defaultLogo = DefaultLogo

// 配置ElementUI
Vue.use(ElementUI, { size: 'medium' })

// 配置axios
axios.defaults.baseURL = process.env.VUE_APP_API_URL || 'http://localhost:8000/api'
// 请求拦截器，添加token到请求头
axios.interceptors.request.use(config => {
  const token = store.getters.token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, error => {
  return Promise.reject(error)
})

// 响应拦截器，处理token过期等问题
axios.interceptors.response.use(response => {
  return response
}, error => {
  if (error.response && error.response.status === 401) {
    // token过期，清除用户信息并跳转到登录页
    store.dispatch('user/logout')
    router.push('/login')
  }
  return Promise.reject(error)
})

Vue.prototype.$http = axios
Vue.config.productionTip = false

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
