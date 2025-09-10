import './assets/main.css'

import { createApp } from 'vue'
import App from './App.vue'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'

const app = createApp(App)

// 配置 Ant Design 主题
app.use(Antd, {
  theme: {
    token: {
      // 模态框主题配置
      colorBgElevated: '#1a1a1a', // 模态框背景色
      colorText: '#ffffff', // 文字颜色
      colorTextHeading: '#ffffff', // 标题文字颜色
      colorBorder: '#444444', // 边框颜色
    },
    components: {
      Modal: {
        contentBg: '#1a1a1a', // 模态框内容背景
        headerBg: '#1a1a1a', // 模态框头部背景
        titleColor: '#ffffff', // 标题颜色
      }
    }
  }
})

app.mount('#app')
