// Sonidos y notificaciones del sistema operativo para los avisos de la campanita.
//
// Sonidos: frontend/public/sounds/ (se sirven en /mesa_ayuda/sounds/).
// Si falta el archivo, suena un tono generado por el navegador.
const BASE = import.meta.env.BASE_URL

const SOUNDS = {
  new_ticket: `${BASE}sounds/nuevo-ticket.mp3`,
  ticket_update: `${BASE}sounds/notificacion.mp3`,
}

const MUTE_KEY = 'mesa_bell_muted'

export function isMuted() {
  try {
    return localStorage.getItem(MUTE_KEY) === '1'
  } catch {
    return false
  }
}

export function setMuted(value) {
  try {
    localStorage.setItem(MUTE_KEY, value ? '1' : '0')
  } catch {
    // sin almacenamiento: solo dura esta sesión
  }
}

// Los navegadores no tienen un permiso de "sonido": solo dejan reproducir audio
// después de que el usuario hizo clic o tecleó algo en la página.
export function audioAllowed() {
  return navigator.userActivation ? navigator.userActivation.hasBeenActive : true
}

export const systemNotificationsSupported = typeof window !== 'undefined' && 'Notification' in window

export function systemPermission() {
  return systemNotificationsSupported ? Notification.permission : 'unsupported'
}

// ¿Falta que el usuario active algo? (sonido bloqueado o permiso de notificaciones sin responder)
export function needsActivation() {
  return !audioAllowed() || systemPermission() === 'default'
}

export async function requestSystemPermission() {
  if (systemPermission() !== 'default') return systemPermission()
  try {
    return await Notification.requestPermission()
  } catch {
    return systemPermission()
  }
}

// Devuelve false si el navegador bloqueó el audio (falta un clic del usuario)
export async function playSound(kind) {
  const src = SOUNDS[kind] ?? SOUNDS.ticket_update
  try {
    const audio = new Audio(src)
    audio.volume = 0.8
    await audio.play()
    return true
  } catch (e) {
    if (e?.name === 'NotAllowedError') return false
    // El archivo no existe o no se pudo leer: tono de respaldo
    return chime()
  }
}

let audioCtx = null

function chime() {
  try {
    audioCtx ??= new (window.AudioContext || window.webkitAudioContext)()
    if (audioCtx.state === 'suspended') audioCtx.resume()
    const now = audioCtx.currentTime
    ;[880, 1318.5].forEach((freq, i) => {
      const osc = audioCtx.createOscillator()
      const gain = audioCtx.createGain()
      osc.type = 'sine'
      osc.frequency.value = freq
      const start = now + i * 0.14
      gain.gain.setValueAtTime(0.0001, start)
      gain.gain.exponentialRampToValueAtTime(0.18, start + 0.02)
      gain.gain.exponentialRampToValueAtTime(0.0001, start + 0.35)
      osc.connect(gain).connect(audioCtx.destination)
      osc.start(start)
      osc.stop(start + 0.4)
    })
    return true
  } catch {
    return false
  }
}

// Notificación del sistema operativo: solo cuando la pestaña no está a la vista
// (si está a la vista, ya se muestra la tarjeta dentro de la página).
export function showSystemNotification(notification, onClick) {
  if (systemPermission() !== 'granted' || !document.hidden) return
  try {
    const n = new Notification(notification.title, {
      body: notification.body ?? '',
      icon: `${BASE}favicon.svg`,
      tag: `mesa-aviso-${notification.id}`,
    })
    n.onclick = () => {
      window.focus()
      onClick?.()
      n.close()
    }
  } catch {
    // algunos navegadores móviles no permiten crearlas desde la página
  }
}
