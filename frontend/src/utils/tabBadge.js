// Señal en la pestaña del navegador para los avisos sin leer (como Gmail):
// - Contador en el título: "(3) Mesa de Ayuda EmPack".
// - Punto rojo sobre el ícono de la pestaña.
// - Si llega un aviso con la pestaña en segundo plano, el título parpadea hasta volver a ella.
const COUNT_PREFIX = /^\(\d+\+?\) /
const FLASH_TEXT = '🔴 Nuevo aviso'
const FLASH_MS = 1000

let unread = 0
let flashTimer = null
let flashOn = false
let baseIcon = null
let badgeIcon = null

function baseTitle() {
  return document.title.replace(COUNT_PREFIX, '').replace(`${FLASH_TEXT} · `, '')
}

function renderTitle() {
  const title = baseTitle()
  const count = unread > 99 ? '99+' : unread
  if (flashOn) document.title = `${FLASH_TEXT} · ${title}`
  else document.title = unread ? `(${count}) ${title}` : title
}

function iconLink() {
  return document.querySelector('link[rel~="icon"]')
}

// El ícono con punto se dibuja una sola vez en un canvas a partir del ícono original
function buildBadgeIcon() {
  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => {
      try {
        const size = 64
        const canvas = document.createElement('canvas')
        canvas.width = size
        canvas.height = size
        const ctx = canvas.getContext('2d')
        ctx.drawImage(img, 0, 0, size, size)
        ctx.beginPath()
        ctx.arc(size - 16, 16, 15, 0, Math.PI * 2)
        ctx.fillStyle = '#E5242B'
        ctx.fill()
        ctx.lineWidth = 4
        ctx.strokeStyle = '#FFFFFF'
        ctx.stroke()
        resolve(canvas.toDataURL('image/png'))
      } catch {
        resolve(null)
      }
    }
    img.onerror = () => resolve(null)
    img.src = baseIcon
  })
}

async function renderIcon() {
  const link = iconLink()
  if (!link) return
  baseIcon ??= link.href
  if (!unread) {
    link.href = baseIcon
    return
  }
  badgeIcon ??= await buildBadgeIcon()
  // Pudo leerse todo mientras se dibujaba el ícono
  if (badgeIcon && unread) link.href = badgeIcon
}

function stopFlash() {
  clearInterval(flashTimer)
  flashTimer = null
  flashOn = false
  renderTitle()
}

export function setUnreadBadge(count) {
  unread = Math.max(0, count || 0)
  if (!unread) stopFlash()
  renderTitle()
  renderIcon()
}

// Solo parpadea si la pestaña no está a la vista: a la vista ya salen las tarjetas
export function flashTab() {
  if (!document.hidden || flashTimer) return
  flashTimer = setInterval(() => {
    flashOn = !flashOn
    renderTitle()
  }, FLASH_MS)
}

if (typeof document !== 'undefined') {
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) stopFlash()
  })
}
