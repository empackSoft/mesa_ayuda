<script setup>
import { computed, onMounted, ref } from 'vue'
import http, { errorMessage } from '../api/http'
import BarList from '../components/BarList.vue'
import { formatDuration } from '../utils/format'
import { PRIORITY_LABELS, STATUS_LABELS } from '../utils/labels'

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
const active = computed(() => total.value - (statusCounts.value.closed ?? 0))

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
    <!-- Indicadores principales -->
    <v-row>
      <v-col cols="12" sm="6" lg="3">
        <v-card class="pa-5 h-100">
          <div class="tile-label">Tickets activos</div>
          <div class="tile-value">{{ active }}</div>
          <div class="text-body-2 text-secondary-label">de {{ total }} en total</div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" lg="3">
        <v-card class="pa-5 h-100">
          <div class="tile-label">Sin atender</div>
          <div class="tile-value">{{ statusCounts.open ?? 0 }}</div>
          <div class="text-body-2 text-secondary-label">en estado Abierto</div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" lg="3">
        <v-card class="pa-5 h-100">
          <div class="tile-label">Tiempo promedio de resolución</div>
          <div class="tile-value">{{ formatDuration(times.average_seconds_general) }}</div>
          <div class="text-body-2 text-secondary-label">
            {{ times.total_resolved ?? 0 }} ticket(s) resuelto(s)
          </div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" lg="3">
        <v-card class="pa-5 h-100">
          <div class="tile-label">Prioridad urgente</div>
          <div class="tile-value">{{ data.priority_counts?.urgent ?? 0 }}</div>
          <div class="text-body-2 text-secondary-label">sin cerrar</div>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-1">
      <v-col cols="12" md="6" lg="4">
        <v-card class="pa-5 h-100">
          <div class="section-title">Tickets por estado</div>
          <BarList :items="byStatus" />
        </v-card>
      </v-col>
      <v-col cols="12" md="6" lg="4">
        <v-card class="pa-5 h-100">
          <div class="section-title">Tickets abiertos por prioridad</div>
          <p class="text-caption text-secondary-label mb-4">Todos los tickets, incluidos los cerrados.</p>
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

    <v-row class="mt-1">
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
.tile-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--app-text-secondary);
}
.tile-value {
  font-size: 34px;
  font-weight: 600;
  letter-spacing: -0.03em;
  line-height: 1.2;
  margin: 6px 0 2px;
  font-variant-numeric: tabular-nums;
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
