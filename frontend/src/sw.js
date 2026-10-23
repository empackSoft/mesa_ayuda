// Service worker de Mesa de Ayuda: permite instalarla como app.
// No guarda datos de tickets: la API siempre va directo al servidor.
// VERSION la pone el build (vite.config.js); al cambiar, el navegador detecta la versión nueva.
const VERSION = '__BUILD_ID__'
const CACHE = `mesa-ayuda-${VERSION}`
const BASE = '/mesa_ayuda/'

const OFFLINE_PAGE = `<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sin conexión · Mesa de Ayuda</title>
<style>
  body { margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center;
    background: #F5F5F7; color: #4A5568; font-family: system-ui, -apple-system, "Segoe UI", Arial, sans-serif;
    padding: 24px 16px; box-sizing: border-box; text-align: center; }
  .card { max-width: 420px; background: #fff; border-radius: 20px; padding: 32px 24px;
    box-shadow: 0 12px 40px rgba(16, 24, 40, .08); }
  h1 { color: #1B2A4A; font-size: 22px; margin: 0 0 10px; }
  p { margin: 0 0 20px; line-height: 1.6; }
  button { background: #1B2A4A; color: #fff; border: 0; border-radius: 999px; padding: 10px 22px;
    font-size: 15px; cursor: pointer; }
</style></head>
<body><div class="card">
  <h1>Sin conexión</h1>
  <p>No pudimos conectar con la Mesa de Ayuda. Revisa tu internet e inténtalo de nuevo.</p>
  <button onclick="location.reload()">Reintentar</button>
</div></body></html>`

self.addEventListener('install', () => {
  // Espera en "waiting" hasta que el usuario acepte la actualización (ver utils/pwa.js)
})

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys()
    await Promise.all(keys.filter((k) => k.startsWith('mesa-ayuda-') && k !== CACHE).map((k) => caches.delete(k)))
    await self.clients.claim()
  })())
})

self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') self.skipWaiting()
})

self.addEventListener('fetch', (event) => {
  const { request } = event
  if (request.method !== 'GET') return
  const url = new URL(request.url)
  if (url.origin !== self.location.origin || !url.pathname.startsWith(BASE)) return
  if (url.pathname.startsWith(`${BASE}api/`)) return

  // Páginas: siempre del servidor (versión al día); sin red, aviso de "Sin conexión"
  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).catch(() => new Response(OFFLINE_PAGE, {
      status: 503,
      headers: { 'Content-Type': 'text/html; charset=utf-8' },
    })))
    return
  }

  // JS/CSS con hash: nunca cambian, se sirven de la caché
  if (url.pathname.startsWith(`${BASE}assets/`)) {
    event.respondWith((async () => {
      const cache = await caches.open(CACHE)
      const cached = await cache.match(request)
      if (cached) return cached
      const response = await fetch(request)
      if (response.ok) cache.put(request, response.clone())
      return response
    })())
  }
})
