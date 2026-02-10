import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import router from './router'
import { createPinia } from 'pinia'
import './style.css'
import './styles/index.css'
import './styles/element-plus.css'
import App from './App.vue'
import { initUserInfo } from './utils/auth'

const app = createApp(App)
const pinia = createPinia()

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus, {
  locale: zhCn,
})


app.use(pinia)

// 在路由挂载前初始化用户信息
initUserInfo().finally(() => {
  app.use(router)
  app.mount('#app')
})
