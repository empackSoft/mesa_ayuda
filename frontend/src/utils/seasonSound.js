import { isMuted } from './alerts'

// Sonido de bienvenida de temporada: suena una vez al iniciar sesión.
// Navidad: coro de "Jingle Bells" (dominio público) con timbre de campana, generado
// por el navegador (sin archivo de audio). Dura ~8 s y se corta a los 10 s como máximo.
// Respeta el botón de silencio de la campanita.

const MAX_SECONDS = 10
const BEAT = 0.26 // segundos por tiempo

// [nota, tiempos]
const JINGLE = [
  ['E5', 1], ['E5', 1], ['E5', 2],
  ['E5', 1], ['E5', 1], ['E5', 2],
  ['E5', 1], ['G5', 1], ['C5', 1.5], ['D5', 0.5], ['E5', 4],
  ['F5', 1], ['F5', 1], ['F5', 1.5], ['F5', 0.5],
  ['F5', 1], ['E5', 1], ['E5', 1], ['E5', 0.5], ['E5', 0.5],
  ['E5', 1], ['D5', 1], ['D5', 1], ['E5', 1],
  ['D5', 2], ['G5', 2],
]

const SEMITONES = { C: -9, D: -7, E: -5, F: -4, G: -2, A: 0, B: 2 }
function freq(note) {
  const octave = Number(note.slice(-1))
  return 440 * 2 ** ((SEMITONES[note[0]] + (octave - 4) * 12) / 12)
}

// Campana: fundamental + parciales inarmónicos que se apagan rápido
function bell(ctx, out, f, at, length) {
  const partials = [[1, 0.6], [2.0, 0.25], [2.76, 0.12], [5.4, 0.05]]
  for (const [ratio, gain] of partials) {
    const osc = ctx.createOscillator()
    const g = ctx.createGain()
    osc.type = 'sine'
    osc.frequency.value = f * ratio
    const decay = Math.min(1.6, 0.35 + length) / ratio ** 0.5
    g.gain.setValueAtTime(0.0001, at)
    g.gain.exponentialRampToValueAtTime(gain, at + 0.008)
    g.gain.exponentialRampToValueAtTime(0.0001, at + decay)
    osc.connect(g).connect(out)
    osc.start(at)
    osc.stop(at + decay + 0.05)
  }
}

// Cascabel de trineo en cada tiempo: ruido corto y agudo
function jingle(ctx, out, at) {
  const len = Math.floor(ctx.sampleRate * 0.08)
  const buffer = ctx.createBuffer(1, len, ctx.sampleRate)
  const data = buffer.getChannelData(0)
  for (let i = 0; i < len; i++) data[i] = (Math.random() * 2 - 1) * (1 - i / len) ** 3
  const src = ctx.createBufferSource()
  src.buffer = buffer
  const hp = ctx.createBiquadFilter()
  hp.type = 'highpass'
  hp.frequency.value = 6000
  const g = ctx.createGain()
  g.gain.value = 0.12
  src.connect(hp).connect(g).connect(out)
  src.start(at)
}

function playJingleBells() {
  const AudioCtx = window.AudioContext || window.webkitAudioContext
  if (!AudioCtx) return
  const ctx = new AudioCtx()
  const master = ctx.createGain()
  master.gain.value = 0.22
  master.connect(ctx.destination)

  let t = ctx.currentTime + 0.1
  const start = t
  for (const [note, beats] of JINGLE) {
    bell(ctx, master, freq(note), t, beats * BEAT)
    t += beats * BEAT
  }
  for (let b = start; b < t; b += BEAT) jingle(ctx, master, b)

  // Corte suave y cierre a los 10 s como máximo
  const end = Math.min(t + 1.2, start + MAX_SECONDS)
  master.gain.setValueAtTime(0.22, end - 0.5)
  master.gain.linearRampToValueAtTime(0.0001, end)
  setTimeout(() => ctx.close().catch(() => {}), (end - ctx.currentTime + 0.2) * 1000)
}

const GREETINGS = {
  navidad: playJingleBells,
}

export function playSeasonGreeting(season) {
  if (isMuted()) return
  try {
    GREETINGS[season]?.()
  } catch {
    // sin audio: no pasa nada
  }
}
