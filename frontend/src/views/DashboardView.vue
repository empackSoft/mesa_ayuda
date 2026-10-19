<script setup>
import { computed, onMounted, ref } from 'vue'
import http, { errorMessage } from '../api/http'
import BarList from '../components/BarList.vue'
import TrendAreaChart from '../components/TrendAreaChart.vue'
import HeatmapGrid from '../components/HeatmapGrid.vue'
import { formatDuration } from '../utils/format'
import {
  LOCATION_TYPE_LABELS, LOCATION_TYPE_PLURALS, PRIORITY_LABELS, RATING_LABELS, STATUS_LABELS, isFinal,
} from '../utils/labels'

const data = ref(null)
const loading = ref(false)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const { data: result } = await http.get('/dashboard/')
    data.value = result
  } catch (e) {
    error.value = errorMessage(e, 'No se pudo cargar el dashboard')
  } finally {
    loading.value = false
  }
}

onMounted(load)

const STATUSES = Object.keys(STATUS_LABELS)
const PRIORITIES = Object.keys(PRIORITY_LABELS)

const statusCounts = computed(() => data.value?.status_counts ?? {})
const total = computed(() => Object.values(statusCounts.value).reduce((a, b) => a + b, 0))
const active = computed(() =>
  Object.entries(statusCounts.value).reduce((a, [s, n]) => (isFinal(s) ? a : a + n), 0),
)

const byStatus = computed(() =>
  STATUSES.map((s) => ({ key: s, label: STATUS_LABELS[s], value: statusCounts.value[s] ?? 0 })),
)

const byPriority = computed(() =>
  [...PRIORITIES].reverse().map((p) => ({
    key: p,
    label: PRIORITY_LABELS[p],
    value: data.value?.priority_counts?.[p] ?? 0,
  })),
)

const times = computed(() => data.value?.resolution_times ?? {})

// --- Encuesta de satisfacción ---
const satisfaction = computed(() => data.value?.satisfaction ?? { total: 0, by_rating: {} })
const byRating = computed(() =>
  [5, 4, 3, 2, 1].map((r) => ({
    key: r,
    label: `${r} ★ ${RATING_LABELS[r]}`,
    value: satisfaction.value.by_rating?.[r] ?? 0,
  })),
)
const autoPct = computed(() =>
  satisfaction.value.total ? Math.round((satisfaction.value.auto / satisfaction.value.total) * 100) : 0,
)

// --- Tendencia diaria (creados vs resueltos) ---
// Colores validados para daltonismo; azul y dorado de la paleta EmPack
const SERIES = [
  { key: 'created', label: 'Creados', color: '#2B5797' },
  { key: 'resolved', label: 'Resueltos', color: '#C98A2E' },
]
const RANGES = [
  { value: 90, label: '3 meses', caption: 'últimos 3 meses' },
  { value: 30, label: '30 días', caption: 'últimos 30 días' },
  { value: 7, label: '7 días', caption: 'últimos 7 días' },
]
const range = ref(30)
const rangeCaption = computed(() => RANGES.find((r) => r.value === range.value)?.caption)

const trend = computed(() => data.value?.trend ?? [])
const trendPoints = computed(() => trend.value.slice(-range.value))
const rangeTotals = computed(() =>
  Object.fromEntries(SERIES.map((s) => [s.key, trendPoints.value.reduce((a, p) => a + (p[s.key] ?? 0), 0)])),
)

function sumCreated(fromEnd, length) {
  const end = trend.value.length - fromEnd
  return trend.value.slice(Math.max(0, end - length), end).reduce((a, p) => a + p.created, 0)
}
const createdThisWeek = computed(() => sumCreated(0, 7))
const createdLastWeek = computed(() => sumCreated(7, 7))
const weekDelta = computed(() => createdThisWeek.value - createdLastWeek.value)
const weekText = computed(() => {
  const d = weekDelta.value
  if (d === 0) return 'Igual que la semana pasada'
  return d > 0 ? `${d} más que la semana pasada` : `${-d} menos que la semana pasada`
})

const unattendedPct = computed(() =>
  active.value ? Math.round(((statusCounts.value.open ?? 0) / active.value) * 100) : 0,
)
const urgent = computed(() => data.value?.priority_counts?.urgent ?? 0)

// --- Categorías: las 7 con más tickets y el resto junto en "Otras" ---
const TOP_CATEGORIES = 7
const byCategory = computed(() => {
  const list = data.value?.category_counts ?? []
  const top = list.slice(0, TOP_CATEGORIES)
  const rest = list.slice(TOP_CATEGORIES)
  const items = top.map((c) => ({
    key: c.incidencia_id,
    label: c.name,
    value: c.total,
    text: `${c.total} · ${c.open} sin cerrar`,
  }))
  if (rest.length) {
    const total = rest.reduce((a, c) => a + c.total, 0)
    const open = rest.reduce((a, c) => a + c.open, 0)
    items.push({ key: 'otras', label: `Otras (${rest.length})`, value: total, text: `${total} · ${open} sin cerrar` })
  }
  return items
})

// --- Antigüedad de los tickets sin resolver ---
const AGING_LABELS = {
  lt_1d: 'Menos de 1 día',
  '1_3d': '1 a 3 días',
  '3_7d': '3 a 7 días',
  '1_4w': '1 a 4 semanas',
  gt_4w: 'Más de 4 semanas',
}
const byAging = computed(() =>
  Object.entries(AGING_LABELS).map(([key, label]) => ({
    key,
    label,
    value: data.value?.open_aging?.[key] ?? 0,
  })),
)
const unresolvedTotal = computed(() => byAging.value.reduce((a, i) => a + i.value, 0))
const oldUnresolved = computed(() => (data.value?.open_aging?.['1_4w'] ?? 0) + (data.value?.open_aging?.gt_4w ?? 0))

// --- Tickets por ubicación (filtro por tipo; las 10 con más tickets o todas) ---
const LOCATION_TYPES = Object.keys(LOCATION_TYPE_LABELS)
const TOP_LOCATIONS = 10
const locationType = ref('all')
const showAllLocations = ref(false)
const locationCounts = computed(() =>
  (data.value?.location_counts ?? []).filter((l) => locationType.value === 'all' || l.type === locationType.value),
)
const byLocation = computed(() =>
  (showAllLocations.value ? locationCounts.value : locationCounts.value.slice(0, TOP_LOCATIONS)).map((l) => ({
    key: l.location_id ?? 'none',
    label: l.name ?? 'Sin ubicación',
    value: l.total,
    text: `${l.total} · ${l.open} sin cerrar`,
  })),
)
const locationTypeTotals = computed(() => {
  const totals = { all: 0 }
  for (const l of data.value?.location_counts ?? []) {
    totals.all += l.total
    if (l.type) totals[l.type] = (totals[l.type] ?? 0) + l.total
  }
  return totals
})

// --- Distribución de tiempos de resolución ---
const RESOLUTION_BUCKETS = {
  lt_1h: 'Menos de 1 hora',
  '1_4h': '1 a 4 horas',
  '4_24h': '4 a 24 horas',
  '1_3d': '1 a 3 días',
  '3_7d': '3 a 7 días',
  gt_1w: 'Más de 1 semana',
}
const RESOLUTION_PERIODS = [
  { value: 'year', label: 'Último año' },
  { value: 'all', label: 'Todo' },
]
const resolutionPeriod = ref('year')
const resolutionCounts = computed(() => data.value?.resolution_distribution?.[resolutionPeriod.value] ?? {})
const resolvedInPeriod = computed(() => Object.values(resolutionCounts.value).reduce((a, b) => a + b, 0))
const pct = (n) => (resolvedInPeriod.value ? Math.round((n / resolvedInPeriod.value) * 100) : 0)
const byResolution = computed(() =>
  Object.entries(RESOLUTION_BUCKETS).map(([key, label]) => {
    const value = resolutionCounts.value[key] ?? 0
    return { key, label, value, text: `${value} · ${pct(value)}%` }
  }),
)
const resolvedSameDayPct = computed(() =>
  pct(['lt_1h', '1_4h', '4_24h'].reduce((a, k) => a + (resolutionCounts.value[k] ?? 0), 0)),
)

const kpis = computed(() => [
  {
    key: 'active',
    label: 'Tickets activos',
    icon: 'ticket',
    value: active.value,
    foot: `${createdThisWeek.value} nuevo(s) en 7 días`,
    footIcon: weekDelta.value > 0 ? 'trending-up' : weekDelta.value < 0 ? 'trending-down' : 'minus',
    hint: `${weekText.value}. ${total.value} tickets en total.`,
  },
  {
    key: 'open',
    label: 'Sin atender',
    icon: 'inbox',
    value: statusCounts.value.open ?? 0,
    foot: `${unattendedPct.value}% de los activos`,
    hint: 'Tickets en estado Abierto: nadie los ha tomado todavía.',
  },
  {
    key: 'time',
    label: 'Tiempo de resolución',
    icon: 'clock',
    value: formatDuration(times.value.average_seconds_general),
    foot: `Promedio de ${times.value.total_resolved ?? 0} resuelto(s)`,
    hint: 'Desde que se crea el ticket hasta que se marca como Resuelto por primera vez.',
  },
  {
    key: 'urgent',
    label: 'Prioridad urgente',
    icon: 'triangle-alert',
    value: urgent.value,
    foot: urgent.value ? 'Atender ya' : 'Al día',
    footIcon: urgent.value ? 'triangle-alert' : 'circle-check',
    tone: urgent.value ? 'error' : 'success',
    hint: `Urgentes sin cerrar. Además hay ${data.value?.priority_counts?.high ?? 0} de prioridad alta.`,
  },
])

const timeByPriority = computed(() =>
  [...PRIORITIES]
    .reverse()
    .filter((p) => times.value.by_priority?.[p] != null)
    .map((p) => ({
      key: p,
      label: PRIORITY_LABELS[p],
      value: times.value.by_priority[p],
      text: formatDuration(times.value.by_priority[p]),
    })),
)

// Une carga de trabajo y tiempos de resolución por técnico
const technicians = computed(() => {
  const rows = new Map()
  for (const t of data.value?.performance_by_technician ?? []) {
    rows.set(t.user_id, { ...t, avg: null, resolved: 0 })
  }
  for (const t of times.value.by_technician ?? []) {
    const row = rows.get(t.user_id) ?? { user_id: t.user_id, name: t.name, total: 0, by_status: {} }
    rows.set(t.user_id, { ...row, avg: t.avg_resolution_seconds, resolved: t.resolved_count })
  }
  return [...rows.values()].sort((a, b) => b.total - a.total)
})
</script>

<template>
  <header class="d-flex flex-wrap align-center ga-3 mb-6">
    <div>
      <h2 class="text-h5">Dashboard</h2>
      <p class="text-body-2 text-secondary-label">Resumen de todos los tickets</p>
    </div>
    <v-spacer />
    <v-btn icon="refresh-cw" variant="text" :loading="loading" title="Actualizar" @click="load" />
  </header>

  <v-alert v-if="error" type="error" class="mb-4">{{ error }}</v-alert>
  <v-progress-linear v-if="loading && !data" indeterminate color="primary" />

  <template v-if="data">
    <!-- Indicadores principales: siempre los 4 en una línea (2x2 solo en celular) -->
    <div class="kpis">
      <v-card v-for="k in kpis" :key="k.key" class="kpi">
        <div :title="k.hint">
        <div class="kpi-head">
          <span class="kpi-label">{{ k.label }}</span>
          <span class="kpi-icon" :class="k.tone && `kpi-icon--${k.tone}`">
            <v-icon :icon="k.icon" size="16" />
          </span>
        </div>
        <div class="kpi-value">{{ k.value }}</div>
        <div class="kpi-foot" :class="k.tone && `text-${k.tone}`">
          <v-icon v-if="k.footIcon" :icon="k.footIcon" size="14" />
          <span>{{ k.foot }}</span>
        </div>
        </div>
      </v-card>
    </div>

    <!-- Tendencia -->
    <v-row dense class="mt-2">
      <v-col cols="12">
        <v-card class="pa-5">
          <div class="d-flex flex-wrap align-start ga-3 mb-3">
            <div>
              <div class="section-title mb-0">Tickets creados y resueltos</div>
              <div class="text-body-2 text-secondary-label">Por día, {{ rangeCaption }}</div>
            </div>
            <v-spacer />
            <v-btn-toggle
              v-model="range"
              mandatory
              density="compact"
              variant="outlined"
              divided
              rounded="lg"
              class="range-toggle"
            >
              <v-btn v-for="r in RANGES" :key="r.value" :value="r.value" size="small">{{ r.label }}</v-btn>
            </v-btn-toggle>
          </div>
          <div class="legend mb-2">
            <span v-for="s in SERIES" :key="s.key" class="legend-item">
              <span class="legend-swatch" :style="{ background: s.color }" />
              {{ s.label }}
              <strong>{{ rangeTotals[s.key] }}</strong>
            </span>
          </div>
          <TrendAreaChart :points="trendPoints" :series="SERIES" />
        </v-card>
      </v-col>
    </v-row>

    <!-- Categorías y antigüedad -->
    <v-row dense class="mt-2">
      <v-col cols="12" md="6">
        <v-card class="pa-5 h-100">
          <div class="section-title">Tickets por categoría</div>
          <p class="text-caption text-secondary-label mb-4">Qué tipo de problema llega más. Total y cuántos siguen sin cerrar.</p>
          <BarList :items="byCategory" empty-text="Aún no hay tickets." />
        </v-card>
      </v-col>
      <v-col cols="12" md="6">
        <v-card class="pa-5 h-100">
          <div class="section-title">Antigüedad de los tickets sin resolver</div>
          <p class="text-caption text-secondary-label mb-4">
            {{ unresolvedTotal }} ticket(s) abiertos, en progreso o pendientes.
            <template v-if="oldUnresolved">
              <strong class="text-error">{{ oldUnresolved }} llevan más de una semana.</strong>
            </template>
          </p>
          <BarList :items="byAging" />
        </v-card>
      </v-col>
    </v-row>

    <!-- Ubicaciones y tiempos de resolución -->
    <v-row dense class="mt-2">
      <v-col cols="12" md="6">
        <v-card class="pa-5 h-100">
          <div class="section-title mb-1">Tickets por ubicación</div>
          <p class="text-caption text-secondary-label mb-3">
            Desde dónde se levantan los tickets. Total y cuántos siguen sin cerrar.
          </p>
          <div class="d-flex flex-wrap ga-2 mb-4">
            <v-chip
              :variant="locationType === 'all' ? 'flat' : 'tonal'"
              :color="locationType === 'all' ? 'primary' : undefined"
              @click="locationType = 'all'"
            >
              Todas · {{ locationTypeTotals.all }}
            </v-chip>
            <v-chip
              v-for="t in LOCATION_TYPES"
              :key="t"
              :variant="locationType === t ? 'flat' : 'tonal'"
              :color="locationType === t ? 'primary' : undefined"
              @click="locationType = t"
            >
              {{ LOCATION_TYPE_PLURALS[t] }} · {{ locationTypeTotals[t] ?? 0 }}
            </v-chip>
          </div>
          <BarList :items="byLocation" empty-text="No hay tickets de este tipo de ubicación." />
          <v-btn
            v-if="locationCounts.length > TOP_LOCATIONS"
            variant="text"
            size="small"
            class="mt-3 px-2"
            :append-icon="showAllLocations ? 'chevron-up' : 'chevron-down'"
            @click="showAllLocations = !showAllLocations"
          >
            {{ showAllLocations ? `Ver solo las ${TOP_LOCATIONS} principales` : `Ver todas (${locationCounts.length})` }}
          </v-btn>
        </v-card>
      </v-col>
      <v-col cols="12" md="6">
        <v-card class="pa-5 h-100">
          <div class="d-flex flex-wrap align-start ga-3 mb-1">
            <div class="section-title mb-0">¿Cuánto tardamos en resolver?</div>
            <v-spacer />
            <v-btn-toggle
              v-model="resolutionPeriod"
              mandatory
              density="compact"
              variant="outlined"
              divided
              rounded="lg"
              class="range-toggle"
            >
              <v-btn v-for="p in RESOLUTION_PERIODS" :key="p.value" :value="p.value" size="small">{{ p.label }}</v-btn>
            </v-btn-toggle>
          </div>
          <p class="text-caption text-secondary-label mb-4">
            {{ resolvedInPeriod }} ticket(s) resueltos<template v-if="resolutionPeriod === 'year'"> de los creados en el último año</template>.
            <template v-if="resolvedInPeriod"><strong>{{ resolvedSameDayPct }}%</strong> se resolvió en menos de un día.</template>
            El promedio puede engañar; aquí se ve si hay casos que tardan mucho.
          </p>
          <BarList :items="byResolution" empty-text="Aún no hay tickets resueltos." />
        </v-card>
      </v-col>
    </v-row>

    <!-- Satisfacción -->
    <v-row dense class="mt-2">
      <v-col cols="12" md="5">
        <v-card class="pa-5 h-100">
          <div class="section-title">Satisfacción del servicio</div>
          <p class="text-caption text-secondary-label mb-4">
            Encuesta obligatoria al cerrar cada ticket.
          </p>
          <template v-if="satisfaction.total">
            <div class="d-flex align-center ga-3 mb-4">
              <span class="sat-average">{{ satisfaction.average?.toFixed(1) }}</span>
              <div>
                <v-rating
                  :model-value="satisfaction.average"
                  readonly
                  half-increments
                  density="compact"
                  size="20"
                  color="grey-lighten-1"
                  active-color="secondary"
                />
                <div class="text-caption text-secondary-label">
                  {{ satisfaction.total }} encuesta(s) · {{ autoPct }}% en automático (sin respuesta)
                </div>
              </div>
            </div>
            <BarList :items="byRating" />
          </template>
          <p v-else class="text-body-2 text-secondary-label">Aún no hay encuestas contestadas.</p>
        </v-card>
      </v-col>
      <v-col cols="12" md="7">
        <v-card class="pa-5 h-100">
          <div class="section-title">Últimos comentarios</div>
          <p class="text-caption text-secondary-label mb-4">Lo que escribieron los usuarios al calificar.</p>
          <p v-if="!satisfaction.recent_comments?.length" class="text-body-2 text-secondary-label">
            Aún no hay comentarios.
          </p>
          <div v-for="c in satisfaction.recent_comments" :key="c.ticket_id" class="sat-comment">
            <div class="d-flex align-center ga-2 mb-1">
              <RouterLink :to="{ name: 'ticket-detail', params: { id: c.ticket_id } }" class="text-body-2">
                #{{ c.ticket_id }}
              </RouterLink>
              <span class="text-body-2 sat-stars">{{ '★'.repeat(c.rating) }}{{ '☆'.repeat(5 - c.rating) }}</span>
            </div>
            <div class="text-body-2 sat-text">{{ c.comment }}</div>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Picos de trabajo -->
    <v-row dense class="mt-2">
      <v-col cols="12">
        <v-card class="pa-5">
          <div class="section-title mb-0">¿Cuándo llegan los tickets?</div>
          <p class="text-caption text-secondary-label mb-4">
            Tickets creados por día y hora en los últimos 3 meses (hora del centro de México).
            Sirve para saber en qué horarios hace falta más personal de soporte.
          </p>
          <HeatmapGrid :cells="data.activity_heatmap ?? []" />
        </v-card>
      </v-col>
    </v-row>

    <v-row dense class="mt-2">
      <v-col cols="12" md="6" lg="4">
        <v-card class="pa-5 h-100">
          <div class="section-title">Tickets por estado</div>
          <p class="text-caption text-secondary-label mb-4">Incluye los cerrados.</p>
          <BarList :items="byStatus" />
        </v-card>
      </v-col>
      <v-col cols="12" md="6" lg="4">
        <v-card class="pa-5 h-100">
          <div class="section-title">Tickets abiertos por prioridad</div>
          <p class="text-caption text-secondary-label mb-4">Solo tickets sin cerrar.</p>
          <BarList :items="byPriority" />
        </v-card>
      </v-col>
      <v-col cols="12" lg="4">
        <v-card class="pa-5 h-100">
          <div class="section-title">Tiempo promedio de resolución por prioridad</div>
          <p class="text-caption text-secondary-label mb-4">
            Desde que se crea el ticket hasta que se marca como Resuelto por primera vez.
          </p>
          <BarList :items="timeByPriority" empty-text="Aún no hay tickets resueltos." />
        </v-card>
      </v-col>

    </v-row>

    <v-row dense class="mt-2">
      <v-col cols="12">
        <v-card>
          <div class="section-title pa-5 pb-2">Rendimiento por técnico</div>
          <v-table v-if="technicians.length" density="comfortable" class="tech-table">
            <thead>
              <tr>
                <th>Técnico</th>
                <th class="text-right">Asignados</th>
                <th v-for="s in STATUSES" :key="s" class="text-right d-none d-sm-table-cell">
                  {{ STATUS_LABELS[s] }}
                </th>
                <th class="text-right">Tiempo prom.</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in technicians" :key="t.user_id">
                <td class="font-weight-medium">{{ t.name }}</td>
                <td class="text-right num">{{ t.total }}</td>
                <td v-for="s in STATUSES" :key="s" class="text-right num d-none d-sm-table-cell">
                  {{ t.by_status?.[s] ?? 0 }}
                </td>
                <td class="text-right num">{{ formatDuration(t.avg) }}</td>
              </tr>
            </tbody>
          </v-table>
          <p v-else class="text-body-2 text-secondary-label px-5 pb-5">Aún no hay tickets asignados.</p>
        </v-card>
      </v-col>
    </v-row>
  </template>
</template>

<style scoped>
.sat-average {
  font-size: 40px;
  font-weight: 600;
  letter-spacing: -0.03em;
  line-height: 1;
}
.sat-comment + .sat-comment {
  border-top: 1px solid var(--app-hairline);
  margin-top: 12px;
  padding-top: 12px;
}
.sat-stars {
  color: rgb(var(--v-theme-secondary));
  letter-spacing: 1px;
}
.sat-text {
  white-space: pre-wrap;
}
.kpis {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}
@media (max-width: 599px) {
  .kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
.kpi {
  padding: 12px 14px;
  background: linear-gradient(180deg, rgba(11, 40, 121, 0.035), #fff 70%);
}
.kpi-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.kpi-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--app-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.kpi-icon {
  flex-shrink: 0;
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: rgba(11, 40, 121, 0.07);
  color: rgb(var(--v-theme-primary));
}
.kpi-icon--error {
  background: rgba(191, 8, 17, 0.08);
  color: rgb(var(--v-theme-error));
}
.kpi-icon--success {
  background: rgba(30, 123, 69, 0.09);
  color: rgb(var(--v-theme-success));
}
.kpi-value {
  font-size: clamp(28px, 3vw, 36px);
  font-weight: 600;
  letter-spacing: -0.03em;
  line-height: 1.15;
  margin: 4px 0 4px;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.kpi-foot {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--app-text-secondary);
  white-space: nowrap;
  overflow: hidden;
}
.kpi-foot span {
  overflow: hidden;
  text-overflow: ellipsis;
}
.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 13px;
  color: var(--app-text-secondary);
}
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.legend-item strong {
  color: var(--app-text);
  font-variant-numeric: tabular-nums;
}
.legend-swatch {
  width: 10px;
  height: 10px;
  border-radius: 3px;
}
.range-toggle .v-btn {
  text-transform: none;
  letter-spacing: 0;
}
.section-title {
  font-weight: 600;
  margin-bottom: 16px;
}
.num {
  font-variant-numeric: tabular-nums;
}
.tech-table :deep(th) {
  font-size: 12px !important;
  color: var(--app-text-secondary) !important;
  font-weight: 500 !important;
}
</style>
