<script setup>
import { computed } from 'vue'

// Mapa de calor día de la semana × hora. Una sola tonalidad (azul EmPack): más oscuro = más tickets.
// cells: [{ weekday: 0=lunes..6=domingo, hour: 0..23, count }]  (solo las celdas con valor)
const props = defineProps({
  cells: { type: Array, required: true },
})

const DAYS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
const HOURS = Array.from({ length: 24 }, (_, h) => h)

const lookup = computed(() => {
  const map = {}
  for (const c of props.cells) map[`${c.weekday}-${c.hour}`] = c.count
  return map
})
const max = computed(() => Math.max(0, ...props.cells.map((c) => c.count)))

// 5 pasos de la misma tonalidad, de claro a oscuro
const STEPS = [0.14, 0.3, 0.48, 0.68, 0.9]
function color(count) {
  if (!count || !max.value) return null
  const step = Math.max(0, Math.ceil((count / max.value) * STEPS.length) - 1)
  return `rgba(11, 40, 121, ${STEPS[step]})`
}

function hourLabel(h) {
  return `${String(h).padStart(2, '0')}:00`
}
function tip(day, h, count) {
  return `${DAYS[day]} ${hourLabel(h)}–${hourLabel((h + 1) % 24)}: ${count || 0} ticket(s)`
}
</script>

<template>
  <div v-if="cells.length" class="heatmap-wrap">
    <div class="heatmap" role="table" aria-label="Tickets creados por día y hora">
      <div class="corner" />
      <div v-for="h in HOURS" :key="`h${h}`" class="hour-label" role="columnheader">
        {{ h % 3 === 0 ? h : '' }}
      </div>
      <template v-for="(day, d) in DAYS" :key="day">
        <div class="day-label" role="rowheader">{{ day.slice(0, 3) }}</div>
        <div
          v-for="h in HOURS"
          :key="`${d}-${h}`"
          class="cell"
          :class="{ 'cell--empty': !lookup[`${d}-${h}`] }"
          :style="{ background: color(lookup[`${d}-${h}`]) }"
          :title="tip(d, h, lookup[`${d}-${h}`])"
          role="cell"
        />
      </template>
    </div>
    <div class="scale">
      <span>Menos</span>
      <span class="swatch swatch--empty" />
      <span v-for="a in STEPS" :key="a" class="swatch" :style="{ background: `rgba(11, 40, 121, ${a})` }" />
      <span>Más</span>
      <span class="ms-3">Máximo: {{ max }} ticket(s) en una hora</span>
    </div>
  </div>
  <p v-else class="text-body-2 text-secondary-label">Aún no hay tickets en este periodo.</p>
</template>

<style scoped>
.heatmap-wrap {
  overflow-x: auto;
}
.heatmap {
  display: grid;
  grid-template-columns: 36px repeat(24, minmax(16px, 1fr));
  gap: 3px;
  min-width: 520px;
}
.hour-label {
  font-size: 11px;
  color: var(--app-text-secondary);
  text-align: left;
  font-variant-numeric: tabular-nums;
}
.day-label {
  font-size: 12px;
  color: var(--app-text-secondary);
  display: flex;
  align-items: center;
}
.cell {
  height: 22px;
  border-radius: 4px;
}
.cell--empty {
  background: rgba(0, 0, 0, 0.035);
}
.cell:hover {
  outline: 2px solid rgba(11, 40, 121, 0.9);
  outline-offset: 1px;
}
.scale {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 12px;
  font-size: 12px;
  color: var(--app-text-secondary);
}
.swatch {
  width: 14px;
  height: 14px;
  border-radius: 3px;
}
.swatch--empty {
  background: rgba(0, 0, 0, 0.035);
}
</style>
