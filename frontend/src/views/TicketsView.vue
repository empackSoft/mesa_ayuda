<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { errorMessage } from '../api/http'
import { ticketsApi } from '../api/tickets'
import MascotPeek from '../components/MascotPeek.vue'
import NewTicketDialog from '../components/NewTicketDialog.vue'
import { useAuthStore } from '../stores/auth'
import { isMuted, playSound } from '../utils/alerts'
import { timeAgo, formatDateTime } from '../utils/format'
import {
  PRIORITY_COLORS, PRIORITY_LABELS, STATUS_COLORS, STATUS_LABELS, isFinal, label,
} from '../utils/labels'

const auth = useAuthStore()
const router = useRouter()

// La paginación, búsqueda y orden se hacen en el servidor (ya son miles de tickets)
const tickets = ref([])
const total = ref(0)
const statusCounts = ref({})
const loading = ref(false)
const error = ref('')
const showNew = ref(false)

const search = ref('')
const statusFilter = ref('active')
const priorityFilter = ref(null)
const onlyMine = ref(false)

const page = ref(1)
const itemsPerPage = ref(25)
const sortBy = ref([{ key: 'id', order: 'desc' }])

let requestId = 0

async function load() {
  const current = ++requestId
  loading.value = true
  error.value = ''
  try {
    const sort = sortBy.value[0] ?? { key: 'id', order: 'desc' }
    const result = await ticketsApi.list({
      status: statusFilter.value,
      priority: priorityFilter.value || undefined,
      q: search.value?.trim() || undefined,
      assigned_to_me: onlyMine.value || undefined,
      page: page.value,
      page_size: itemsPerPage.value,
      sort_by: sort.key,
      sort_desc: sort.order === 'desc',
    })
    // Si el usuario siguió escribiendo, se ignora la respuesta vieja
    if (current !== requestId) return
    tickets.value = result.items
    total.value = result.total
    statusCounts.value = result.status_counts
  } catch (e) {
    if (current === requestId) error.value = errorMessage(e, 'No se pudieron cargar los tickets')
  } finally {
    if (current === requestId) loading.value = false
  }
}

// Al cambiar un filtro se regresa a la página 1
function reloadFromFirstPage() {
  if (page.value !== 1) page.value = 1
  else load()
}

watch([statusFilter, priorityFilter, onlyMine], reloadFromFirstPage)

let searchTimer = null
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(reloadFromFirstPage, 350)
})

// v-data-table-server avisa al montarse y al cambiar de página, tamaño u orden
function onOptions(options) {
  page.value = options.page
  itemsPerPage.value = options.itemsPerPage
  sortBy.value = options.sortBy
  load()
}

function sumCounts(match) {
  return Object.entries(statusCounts.value).reduce((a, [s, n]) => (match(s) ? a + n : a), 0)
}

const STATUS_TABS = [
  { value: 'active', title: 'Activos' },
  { value: 'all', title: 'Todos' },
  ...Object.keys(STATUS_LABELS).map((s) => ({ value: s, title: STATUS_LABELS[s] })),
]

const countByTab = computed(() => ({
  active: sumCounts((s) => !isFinal(s)),
  all: sumCounts(() => true),
  ...Object.fromEntries(Object.keys(STATUS_LABELS).map((s) => [s, statusCounts.value[s] ?? 0])),
}))

const hasFilters = computed(() =>
  Boolean(search.value?.trim() || priorityFilter.value || onlyMine.value || statusFilter.value !== 'all'),
)

const priorityItems = Object.entries(PRIORITY_LABELS).map(([value, title]) => ({ value, title }))

const headers = computed(() => [
  { title: '#', key: 'id', width: 70 },
  { title: 'Ticket', key: 'description', sortable: false },
  { title: 'Estado', key: 'status', width: 130 },
  { title: 'Prioridad', key: 'priority', width: 120 },
  ...(auth.isStaff ? [{ title: 'Solicitante', key: 'created_by_user_name', width: 170 }] : []),
  { title: 'Asignado a', key: 'assigned_to_user_name', width: 170 },
  { title: 'Creado', key: 'created_at', width: 130 },
])

function openTicket(_event, { item }) {
  router.push({ name: 'ticket-detail', params: { id: item.id } })
}

// El aviso viaja en history.state para mostrarse ya en el detalle.
// Suena también para quien lo levanta (la campanita no le avisa de su propia acción).
function onCreated(ticket, failed) {
  if (!isMuted()) playSound('new_ticket')
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

    <v-data-table-server
      :headers="headers"
      :items="tickets"
      :items-length="total"
      :loading="loading"
      :page="page"
      :items-per-page="itemsPerPage"
      :items-per-page-options="[10, 25, 50, 100]"
      :sort-by="sortBy"
      must-sort
      hover
      class="tickets-table"
      @update:options="onOptions"
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
        <div v-if="item.feedback_state === 'confirm'" class="text-caption text-warning mt-1">
          Espera confirmación
        </div>
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
          :icon="hasFilters ? 'inbox' : undefined"
          :title="hasFilters ? 'Sin resultados' : 'Aún no hay tickets'"
          :text="hasFilters ? 'Ningún ticket coincide con los filtros.' : 'Cuando se cree un ticket aparecerá aquí.'"
          size="56"
        >
          <template v-if="!hasFilters && !loading" #media>
            <div class="d-flex justify-center mb-2">
              <MascotPeek :size="110" />
            </div>
          </template>
        </v-empty-state>
      </template>
    </v-data-table-server>
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
