import { ref } from 'vue'

// Registro del service worker (instalar como app) y aviso de versión nueva
export const updateReady = ref(false)

let registration = null
const CHECK_EVERY_MS = 30 * 60 * 1000

export function registerServiceWorker() {
  // En desarrollo (vite) no se registra para no cachear nada mientras se programa
  if (!import.meta.env.PROD || !('serviceWorker' in navigator)) return

  window.addEventListener('load', async () => {
    try {
      registration = await navigator.serviceWorker.register(`${import.meta.env.BASE_URL}sw.js`, {
        scope: import.meta.env.BASE_URL,
      })
    } catch {
      return
    }

    // Ya había una versión nueva esperando desde antes
    if (registration.waiting && navigator.serviceWorker.controller) updateReady.value = true

    registration.addEventListener('updatefound', () => {
      const worker = registration.installing
      worker?.addEventListener('statechange', () => {
        // Sin controller es la primera instalación: no hay nada que actualizar
        if (worker.state === 'installed' && navigator.serviceWorker.controller) updateReady.value = true
      })
    })

    // La app puede quedarse abierta días: revisar de vez en cuando y al volver a ella
    setInterval(() => registration.update().catch(() => {}), CHECK_EVERY_MS)
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') registration.update().catch(() => {})
    })
  })
}

export function applyUpdate() {
  const waiting = registration?.waiting
  if (!waiting) {
    window.location.reload()
    return
  }
  navigator.serviceWorker.addEventListener('controllerchange', () => window.location.reload(), { once: true })
  waiting.postMessage({ type: 'SKIP_WAITING' })
}
