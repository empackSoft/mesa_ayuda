<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

// Nieve que cae solo dentro del menú lateral (temporada navideña).
// Canvas encima del menú sin capturar clics; se pausa con la pestaña oculta.
// Si el sistema pide reducir el movimiento (p. ej. Windows con animaciones desactivadas)
// la nieve cae más lenta y sin vaivén, en lugar de desaparecer.
const canvas = ref(null)

// Blanca sobre el fondo azul suave del menú en Navidad
const COLORS = ['#FFFFFF', '#FFFFFF', '#F4F7FF', '#EEF2FF']
const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
const SPEED = reducedMotion ? 0.4 : 1

let flakes = []
let frame = null
let observer = null
let width = 0
let height = 0
let last = 0

const rnd = (a, b) => a + Math.random() * (b - a)

function makeFlake(randomY) {
  const r = rnd(1.8, 4)
  return {
    x: rnd(0, width),
    y: randomY ? rnd(-height, height) : rnd(-40, -5),
    r,
    // Los copos grandes caen un poco más rápido (efecto de profundidad)
    speed: (14 + r * 9 + rnd(0, 8)) * SPEED,
    drift: reducedMotion ? rnd(2, 5) : rnd(8, 20),
    phase: rnd(0, Math.PI * 2),
    wobble: rnd(0.6, 1.4),
    color: COLORS[Math.floor(Math.random() * COLORS.length)],
    alpha: rnd(0.7, 1),
  }
}

function resize() {
  const el = canvas.value
  if (!el) return
  const dpr = window.devicePixelRatio || 1
  width = el.clientWidth
  height = el.clientHeight
  el.width = Math.round(width * dpr)
  el.height = Math.round(height * dpr)
  el.getContext('2d').setTransform(dpr, 0, 0, dpr, 0, 0)
  // Más copos en el menú abierto que en el contraído
  const target = Math.round((width * height) / 3400)
  while (flakes.length < target) flakes.push(makeFlake(true))
  flakes.length = Math.min(flakes.length, target)
}

function draw(now) {
  frame = requestAnimationFrame(draw)
  const dt = Math.min(0.05, (now - last) / 1000 || 0)
  last = now
  if (document.hidden) return

  const ctx = canvas.value.getContext('2d')
  ctx.clearRect(0, 0, width, height)
  // Borde azul tenue para que el copo blanco resalte sobre el fondo claro
  ctx.shadowColor = 'rgba(11, 40, 121, 0.35)'
  ctx.shadowBlur = 3
  for (const f of flakes) {
    f.y += f.speed * dt
    f.phase += f.wobble * dt
    if (f.y - f.r > height) Object.assign(f, makeFlake(false))
    const x = f.x + Math.sin(f.phase) * f.drift
    ctx.globalAlpha = f.alpha
    ctx.fillStyle = f.color
    ctx.beginPath()
    ctx.arc(x, f.y, f.r, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.globalAlpha = 1
}

onMounted(() => {
  observer = new ResizeObserver(resize)
  observer.observe(canvas.value)
  resize()
  frame = requestAnimationFrame(draw)
})

onBeforeUnmount(() => {
  cancelAnimationFrame(frame)
  observer?.disconnect()
})
</script>

<template>
  <canvas ref="canvas" class="sidebar-snow" aria-hidden="true" />
</template>

<style scoped>
.sidebar-snow {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}
</style>
