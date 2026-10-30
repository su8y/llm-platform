import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import viteCompression from 'vite-plugin-compression'
import path from "path";

// https://vitejs.dev/config/
const __dirname = path.dirname(fileURLToPath(import.meta.url))
export default defineConfig(({ mode }) => ({
  optimizeDeps: {
    include: ['ckeditor5'],
    force: true
  },
  build: {
    minify: 'terser',
    chunkSizeWarningLimit: 1000,
    terserOptions: {
      compress: {
        drop_console: false,
        drop_debugger: true,
        passes: 1,
        dead_code: true
      },
      mangle: false, // 난독화 완전 비활성화로 변수 순서 문제 해결
      format: {
        beautify: false,
        comments: false,
      }
    },
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('ckeditor5')) return 'ckeditor'
            if (id.includes('echarts')) return 'echarts'
            if (id.includes('vue-router')) return 'router'
            if (id.includes('vuex') || id.includes('vue-i18n')) return 'state'
            return 'vendor'
          }
        },
        format: 'es',
        exports: 'named'
      },
    }
  },
  plugins: [
    viteCompression({
      algorithm: 'gzip',
      ext: '.gz',
      threshold: 1024,
      deleteOriginFile: false,
    }),
    vue(),
    { src: '~/plugins/local-storage.js' },
    // 개발 환경에서는 프리렌더링 비활성화로 메모리 절약
    ...(mode === 'production' ? [
    ] : [])
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
    dedupe: ['ckeditor5']
  },
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@use "@/styles/base/_variables.scss" as *;`
      }
    }
  }
}))
