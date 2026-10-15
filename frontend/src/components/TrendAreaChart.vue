<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

// Gráfica de área por día (SVG propio, sin librerías).
// points: [{ date: 'YYYY-MM-DD', <serie>: número, ... }]
// series: [{ key, label, color }]  — las áreas se superponen (no se apilan)
const props = defineProps({
  points: { type: Array, required: true },
  series: { type: Array, required: true },
  height: { type: Number, default: 260 },
})

const PAD = { top: 12, right: 12, bottom: 28, left: 32 }
const uid = `trend-${Math.random().toString(36).slice(2, 8)}`

const root = ref(null)
const width = ref(600)
const hover = ref(null) // índice del día bajo el cursor
let observer

onMounted(() => {
  observer = new ResizeObserver(([entry]) => {
    width.value = Math.max(280, entry.contentRect.width)
  })
  observer.observe(root.value)
})
onBeforeUnmount(() => observer?.disconnect())

const innerW = computed(() => width.value - PAD.left - PAD.right)
const innerH = computed(() => props.height - PAD.top - PAD.bottom)

// Máximo "redondo" para el eje Y, con 4 líneas guía de valores enteros
const yTicks = computed(() => {
  const max = Math.max(1, ...props.points.flatMap((p) => props.series.map((s) => p[s.key] ?? 0)))
  const step = Math.max(1, Math.ceil(max / 4))
  return [0, 1, 2, 3, 4].map((i) => i * step)
})
const yMax = computed(() => yTicks.value[yTicks.value.length - 1])

function x(i) {
  const n = props.points.length
  return PAD.left + (n <= 1 ? innerW.value / 2 : (i / (n - 1)) * innerW.value)
}
function y(v) {
  return PAD.top + innerH.value - (v / yMax.value) * innerH.value
}

// Curva monótona (Fritsch–Carlson): suave pero nunca baja de 0 ni inventa picos
function monotonePath(pts) {
  if (pts.length < 2) return pts.length ? `M${pts[0][0]},${pts[0][1]}` : ''
  const n = pts.length
  const dx = [], m = [], t = new Array(n)
  for (let i = 0; i < n - 1; i++) {
    dx[i] = pts[i + 1][0] - pts[i][0]
    m[i] = (pts[i + 1][1] - pts[i][1]) / dx[i]
  }
  t[0] = m[0]
  t[n - 1] = m[n - 2]
  for (let i = 1; i < n - 1; i++) t[i] = m[i - 1] * m[i] <= 0 ? 0 : (m[i - 1] + m[i]) / 2
  for (let i = 0; i < n - 1; i++) {
    if (m[i] === 0) { t[i] = 0; t[i + 1] = 0; continue }
    const a = t[i] / m[i], b = t[i + 1] / m[i], h = a * a + b * b
    if (h > 9) { const k = 3 / Math.sqrt(h); t[i] = k * a * m[i]; t[i + 1] = k * b * m[i] }
  }
  let d = `M${pts[0][0]},${pts[0][1]}`
  for (let i = 0; i < n - 1; i++) {
    const c = dx[i] / 3
    d += ` C${pts[i][0] + c},${pts[i][1] + c * t[i]} ${pts[i + 1][0] - c},${pts[i + 1][1] - c * t[i + 1]} ${pts[i + 1][0]},${pts[i + 1][1]}`
  }
  return d
}

const paths = computed(() =>
  props.series.map((s) => {
    const pts = props.points.map((p, i) => [x(i), y(p[s.key] ?? 0)])
    const line = monotonePath(pts)
    const base = PAD.top + innerH.value
    const area = pts.length ? `${line} L${pts[pts.length - 1][0]},${base} L${pts[0][0]},${base} Z` : ''
    return { ...s, line, area }
  }),
)

function parseDay(iso) {
  const [yy, mm, dd] = iso.split('-').map(Number)
  return new Date(yy, mm - 1, dd)
}
const shortDay = new Intl.DateTimeFormat('es-MX', { day: 'numeric', month: 'short' })
const longDay = new Intl.DateTimeFormat('es-MX', { weekday: 'short', day: 'numeric', month: 'long' })

// ~6 etiquetas en el eje X, sin encimarse
const xTicks = computed(() => {
  const n = props.points.length
  if (!n) return []
  const count = Math.min(n, Math.max(2, Math.floor(innerW.value / 90)))
  const step = (n - 1) / (count - 1 || 1)
  return Array.from({ length: count }, (_, k) => {
    const i = Math.round(k * step)
    return { i, label: shortDay.format(parseDay(props.points[i].date)) }
  })
})

function onMove(event) {
  const n = props.points.length
  if (!n) return
  const rect = root.value.getBoundingClientRect()
  const px = event.clientX - rect.left - PAD.left
  hover.value = Math.min(n - 1, Math.max(0, Math.round((px / innerW.value) * (n - 1))))
}

const tooltip = computed(() => {
  if (hover.value == null) return null
  const p = props.points[hover.value]
  const left = x(hover.value)
  return {
    title: longDay.format(parseDay(p.date)),
    rows: props.series.map((s) => ({ ...s, value: p[s.key] ?? 0 })),
    style: {
      left: `${left}px`,
      transform: left > width.value * 0.65 ? 'translateX(calc(-100% - 12px))' : 'translateX(12px)',
    },
  }
})
</script>

<template>
  <div ref="root" class="trend" :style="{ height: `${height}px` }" @mousemove="onMove" @mouseleave="hover = null">
    <svg :width="width" :height="height" role="img" aria-label="Tickets por día">
      <defs>
        <linearGradient v-for="s in series" :id="`${uid}-${s.key}`" :key="s.key" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" :stop-color="s.color" stop-opacity="0.28" />
          <stop offset="100%" :stop-color="s.color" stop-opacity="0.02" />
        </linearGradient>
      </defs>

      <!-- Líneas guía y eje Y -->
      <g class="grid">
        <line v-for="t in yTicks" :key="t" :x1="PAD.left" :x2="width - PAD.right" :y1="y(t)" :y2="y(t)" />
      </g>
      <g class="axis">
        <text v-for="t in yTicks" :key="t" :x="PAD.left - 8" :y="y(t)" text-anchor="end" dominant-baseline="middle">
          {{ t }}
        </text>
        <text
          v-for="t in xTicks"
          :key="t.i"
          :x="x(t.i)"
          :y="height - 8"
          :text-anchor="t.i === 0 ? 'start' : t.i === points.length - 1 ? 'end' : 'middle'"
        >
          {{ t.label }}
        </text>
      </g>

      <!-- Áreas y líneas -->
      <path v-for="p in paths" :key="`a-${p.key}`" :d="p.area" :fill="`url(#${uid}-${p.key})`" />
      <path v-for="p in paths" :key="`l-${p.key}`" :d="p.line" fill="none" :stroke="p.color" stroke-width="2" stroke-linejoin="round" />

      <!-- Cursor -->
      <g v-if="hover != null">
        <line class="crosshair" :x1="x(hover)" :x2="x(hover)" :y1="PAD.top" :y2="PAD.top + innerH" />
        <circle
          v-for="s in series"
          :key="s.key"
          :cx="x(hover)"
          :cy="y(points[hover][s.key] ?? 0)"
          r="4"
          :fill="s.color"
          stroke="#fff"
          stroke-width="2"
        />
      </g>
    </svg>

    <div v-if="tooltip" class="trend-tooltip" :style="tooltip.style">
      <div class="tt-title">{{ tooltip.title }}</div>
      <div v-for="r in tooltip.rows" :key="r.key" class="tt-row">
        <span class="tt-swatch" :style="{ background: r.color }" />
        <span class="tt-label">{{ r.label }}</span>
        <span class="tt-value">{{ r.value }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.trend {
  position: relative;
  width: 100%;
  cursor: crosshair;
}
svg {
  display: block;
  overflow: visible;
}
.grid line {
  stroke: var(--app-hairline);
  stroke-dasharray: 3 3;
}
.axis text {
  font-size: 11px;
  fill: var(--app-text-secondary);
  font-variant-numeric: tabular-nums;
}
.crosshair {
  stroke: rgba(0, 0, 0, 0.18);
}
.trend-tooltip {
  position: absolute;
  top: 8px;
  pointer-events: none;
  min-width: 150px;
  padding: 8px 10px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid var(--app-hairline);
  box-shadow: var(--app-shadow-float);
  font-size: 12px;
  z-index: 2;
}
.tt-title {
  font-weight: 600;
  margin-bottom: 4px;
  text-transform: capitalize;
}
.tt-row {
  display: flex;
  align-items: center;
  gap: 8px;
  line-height: 1.7;
}
.tt-swatch {
  width: 8px;
  height: 8px;
  border-radius: 2px;
}
.tt-label {
  flex: 1;
  color: var(--app-text-secondary);
}
.tt-value {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
</style>
