import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig(({ command, mode }) => {
  const isDev = command === 'serve'
  
  return {
    plugins: [
      vue(),
      vueDevTools(),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      },
    },
    // 开发环境配置
    server: isDev ? {
      proxy: {
        '/api': {
          target: 'http://localhost:9001',
          changeOrigin: true,
          secure: false
        }
      }
    } : undefined,
    // 生产环境配置
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['vue', 'ant-design-vue']
          }
        }
      }
    }
  }
})
