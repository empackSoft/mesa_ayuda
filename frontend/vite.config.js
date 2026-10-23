import { readFileSync } from 'node:fs'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'
import { defineConfig } from 'vite'

// Service worker (src/sw.js) con un id distinto en cada build, para que el navegador detecte la versión nueva
function serviceWorker() {
  return {
    name: 'mesa-ayuda-sw',
    apply: 'build',
    generateBundle() {
      const source = readFileSync(new URL('./src/sw.js', import.meta.url), 'utf8')
      this.emitFile({
        type: 'asset',
        fileName: 'sw.js',
        source: source.replaceAll('__BUILD_ID__', Date.now().toString(36)),
      })
    },
  }
}

// La app vive bajo /mesa_ayuda/ (mismo prefijo que en producción)
export default defineConfig({
  base: '/mesa_ayuda/',
  plugins: [
    vue(),
    vuetify({ autoImport: true }),
    serviceWorker(),
  ],
  server: {
    port: 5173,
    // En local, la API se toma del nginx de Docker (mismo origen, sin CORS)
    proxy: {
      '/mesa_ayuda/api': 'http://127.0.0.1:8080',
    },
  },
})
