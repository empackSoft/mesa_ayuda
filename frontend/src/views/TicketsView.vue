<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { errorMessage } from '../api/http'
import { ticketsApi } from '../api/tickets'
import MascotPeek from '../components/MascotPeek.vue'
import NewTicketDialog from '../components/NewTicketDialog.vue'
import { useAuthStore } from '../stores/auth'
import { timeAgo, formatDateTime } from '../utils/format'
import {
  PRIORITY_COLORS, PRIORITY_LABELS, STATUS_COLORS, STATUS_LABELS, label,
} from '../utils/labels'

const auth = useAuthStore()
const router = useRouter()

const tickets = ref([])
const loading = ref(false)
const error = ref('')
const showNew = ref(false)

const search = ref('')
const statusFilter = ref('active')
const priorityFilter = ref(null)
const onlyMine = ref(false)

// Se piden todos los tickets visibles y se filtra en el navegador (volumen chico)
async function load() {
  loading.value = true
  error.value = ''
  try {
    tickets.value = await ticketsApi.list()
  } catch (e) {
    error.value = errorMessage(e, 'No se pudieron cargar los tickets')
  } finally {
    loading.value = false
  }
}

onMounted(load)

const STATUS_TABS = [
  { value: 'active', title: 'Activos', match: (t) => t.status !== 'closed' },
  { value: 'all', title: 'Todos', match: () => true },
  ...Object.keys(STATUS_LABELS).map((s) => ({
    value: s,
    title: STATUS_LABELS[s],
    match: (t) => t.status === s,
  })),
]

const countByTab = computed(() =>
  Object.fromEntries(STATUS_TABS.map((tab) => [tab.value, tickets.value.filter(tab.match).length])),
)

const filtered = computed(() => {
  const tab = STATUS_TABS.find((t) => t.value === statusFilter.value)
  const q = search.value.trim().toLowerCase()
  return tickets.value.filter((t) => {
    if (!tab.match(t)) return false
    if (priorityFilter.value && t.priority !== priorityFilter.value) return false
    if (onlyMine.value && t.assigned_to_user_id !== auth.user?.id) return false
    if (!q) return true
    return [
      `#${t.id}`,
      t.description,
      t.incidencia,
      t.subincidencia,
      t.created_by_user_name,
      t.assigned_to_user_name,
    ].some((v) => v?.toLowerCase().includes(q))
  })
})

const priorityItems = Object.entries(PRIORITY_LABELS).map(([value, title]) => ({ value, title }))

const PRIORITY_ORDER = { low: 0, medium: 1, high: 2, urgent: 3 }

const headers = computed(() => [
  { title: '#', key: 'id', width: 70 },
  { title: 'Ticket', key: 'description', sortable: false },
  { title: 'Estado', key: 'status', width: 130 },
  {
    title: 'Prioridad',
    key: 'priority',
    width: 120,
    sortRaw: (a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority],
  },
  ...(auth.isStaff ? [{ title: 'Solicitante', key: 'created_by_user_name', width: 170 }] : []),
  { title: 'Asignado a', key: 'assigned_to_user_name', width: 170 },
  { title: 'Creado', key: 'created_at', width: 130 },
])

function openTicket(_event, { item }) {
  router.push({ name: 'ticket-detail', params: { id: item.id } })
}

// El aviso viaja en history.state para mostrarse ya en el detalle
function onCreated(ticket, failed) {
  const notice = failed.length
    ? { color: 'warning', text: `Ticket #${ticket.id} creado, pero no se pudieron subir: ${failed.join('; ')}` }
    : { color: 'success', text: `Ticket #${ticket.id} creado. Soporte ya fue notificado.` }
  router.push({ name: 'ticket-detail', params: { id: ticket.id }, state: { notice } })
}
</script>

<template>
  <header class="d-flex flex-wrap align-center ga-3 mb-6">
    <div>
      <h2 class="text-h5">{{ auth.isStaff ? 'Tickets' : 'Mis tickets' }}</h2>
      <p class="text-body-2 text-secondary-label">
        {{ auth.isStaff ? 'Solicitudes de todos los usuarios' : 'Tus solicitudes a Soporte' }}
      </p>
    </div>
    <v-spacer />
    <v-btn icon="refresh-cw" variant="text" :loading="loading" title="Actualizar" @click="load" />
    <v-btn color="primary" prepend-icon="plus" @click="showNew = true">Nuevo ticket</v-btn>
  </header>

  <v-alert v-if="error" type="error" class="mb-4">{{ error }}</v-alert>

  <v-chip-group v-model="statusFilter" mandatory selected-class="chip-selected" class="mb-3">
    <v-chip v-for="tab in STATUS_TABS" :key="tab.value" :value="tab.value" variant="text" size="default">
      {{ tab.title }}
      <span class="ml-2 tab-count">{{ countByTab[tab.value] }}</span>
    </v-chip>
  </v-chip-group>

  <v-card>
    <div class="d-flex flex-wrap ga-3 pa-4">
      <v-text-field
        v-model="search"
        prepend-inner-icon="search"
        placeholder="Buscar por número, descripción, categoría o persona"
        hide-details
        clearable
        class="filter-search"
      />
      <v-select
        v-model="priorityFilter"
        :items="priorityItems"
        placeholder="Prioridad"
        hide-details
        clearable
        class="filter-priority"
      />
      <v-switch
        v-if="auth.isStaff"
        v-model="onlyMine"
        label="Asignados a mí"
        color="primary"
        hide-details
        inset
        density="compact"
        class="flex-grow-0"
      />
    </div>

    <v-divider />

    <v-data-table
      :headers="headers"
      :items="filtered"
      :loading="loading"
      :sort-by="[{ key: 'id', order: 'desc' }]"
      :items-per-page="25"
      hover
      class="tickets-table"
      @click:row="openTicket"
    >
      <template #item.id="{ item }">
        <span class="text-secondary-label">#{{ item.id }}</span>
      </template>

      <template #item.description="{ item }">
        <div class="py-3">
          <div class="font-weight-medium">{{ item.incidencia }} · {{ item.subincidencia }}</div>
          <div class="text-body-2 text-secondary-label text-truncate description">{{ item.description }}</div>
        </div>
      </template>

      <template #item.status="{ item }">
        <v-chip :color="STATUS_COLORS[item.status]">{{ label(STATUS_LABELS, item.status) }}</v-chip>
      </template>

      <template #item.priority="{ item }">
        <v-chip :color="PRIORITY_COLORS[item.priority]" variant="text" prepend-icon="flag">
          {{ label(PRIORITY_LABELS, item.priority) }}
        </v-chip>
      </template>

      <template #item.assigned_to_user_name="{ item }">
        <span v-if="item.assigned_to_user_name">{{ item.assigned_to_user_name }}</span>
        <span v-else class="text-secondary-label">Sin asignar</span>
      </template>

      <template #item.created_at="{ item }">
        <span :title="formatDateTime(item.created_at)" class="text-body-2">{{ timeAgo(item.created_at) }}</span>
      </template>

      <template #no-data>
        <v-empty-state
          :icon="tickets.length ? 'inbox' : undefined"
          :title="tickets.length ? 'Sin resultados' : 'Aún no hay tickets'"
          :text="tickets.length ? 'Ningún ticket coincide con los filtros.' : 'Cuando se cree un ticket aparecerá aquí.'"
          size="56"
        >
          <template v-if="!tickets.length && !loading" #media>
            <div class="d-flex justify-center mb-2">
              <MascotPeek :size="110" />
            </div>
          </template>
        </v-empty-state>
      </template>
    </v-data-table>
  </v-card>

  <NewTicketDialog v-model="showNew" @created="onCreated" />
</template>

<style scoped>
.filter-search {
  flex: 1 1 280px;
}
.filter-priority {
  flex: 0 1 180px;
}
.tickets-table :deep(tbody tr) {
  cursor: pointer;
}
.description {
  max-width: 460px;
}
.tab-count {
  font-size: 12px;
  opacity: 0.6;
}
.chip-selected {
  background: rgba(11, 40, 121, 0.08);
  color: rgb(var(--v-theme-primary));
}
</style>
