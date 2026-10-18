<script setup>
import { computed, onMounted, ref } from 'vue'
import http, { errorMessage } from '../api/http'
import { LOCATION_TYPE_ICONS, LOCATION_TYPE_LABELS, LOCATION_TYPE_PLURALS } from '../utils/labels'

// Catálogo de incidencias (categorías), subincidencias (subcategorías) y ubicaciones. Solo admin.
// No se borra nada: se desactiva, para no romper tickets que ya las usan.

const incidencias = ref([])
const subincidencias = ref([])
const locations = ref([])
const newLocation = ref('')
const newLocationType = ref('branch')
const locationSearch = ref('')
const locationTypeFilter = ref('all')
const LOCATION_TYPES = Object.keys(LOCATION_TYPE_LABELS)
const notifyGroups = ref([])
const groupDrafts = ref({}) // { [id]: [correos] } mientras se edita
const savingGroup = ref(null)
const ALWAYS_GROUP = 'always' // va en copia en todos los tickets; no se elige por categoría
const selectedId = ref(null)
const loading = ref(false)
const error = ref('')
const notice = ref({ show: false, text: '', color: 'success' })

const newIncidencia = ref('')
const newSub = ref('')
const savingNew = ref('')

const editing = ref(null) // { kind: 'incidencia' | 'sub', item, name }
const savingEdit = ref(false)

function notify(text, color = 'success') {
  notice.value = { show: true, text, color }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [inc, subs, locationList, groups] = await Promise.all([
      http.get('/incidencias/').then((r) => r.data),
      http.get('/incidencias/subincidencias/all').then((r) => r.data),
      http.get('/locations/').then((r) => r.data),
      http.get('/notify-groups/').then((r) => r.data),
    ])
    incidencias.value = inc
    subincidencias.value = subs
    locations.value = locationList
    notifyGroups.value = groups
    groupDrafts.value = Object.fromEntries(groups.map((g) => [g.id, [...g.emails]]))
    if (!incidencias.value.some((i) => i.id === selectedId.value)) {
      selectedId.value = incidencias.value[0]?.id ?? null
    }
  } catch (e) {
    error.value = errorMessage(e, 'No se pudo cargar el catálogo')
  } finally {
    loading.value = false
  }
}

onMounted(load)

const selected = computed(() => incidencias.value.find((i) => i.id === selectedId.value))

const subsOfSelected = computed(() =>
  subincidencias.value
    .filter((s) => s.incidencia_id === selectedId.value)
    .sort((a, b) => a.name.localeCompare(b.name, 'es')),
)

const subCount = computed(() => {
  const counts = {}
  for (const s of subincidencias.value) {
    if (s.is_active) counts[s.incidencia_id] = (counts[s.incidencia_id] ?? 0) + 1
  }
  return counts
})

async function createIncidencia() {
  const name = newIncidencia.value.trim()
  if (name.length < 2) return
  savingNew.value = 'incidencia'
  try {
    const { data } = await http.post('/incidencias/', { name })
    incidencias.value.push(data)
    incidencias.value.sort((a, b) => a.name.localeCompare(b.name, 'es'))
    selectedId.value = data.id
    newIncidencia.value = ''
    notify(`Categoría "${data.name}" creada`)
  } catch (e) {
    notify(errorMessage(e), 'error')
  } finally {
    savingNew.value = ''
  }
}

async function createSub() {
  const name = newSub.value.trim()
  if (name.length < 2 || !selectedId.value) return
  savingNew.value = 'sub'
  try {
    const { data } = await http.post('/incidencias/subincidencias', {
      incidencia_id: selectedId.value,
      name,
    })
    subincidencias.value.push(data)
    newSub.value = ''
    notify(`Subcategoría "${data.name}" creada`)
  } catch (e) {
    notify(errorMessage(e), 'error')
  } finally {
    savingNew.value = ''
  }
}

async function createLocation() {
  const name = newLocation.value.trim()
  if (name.length < 2) return
  savingNew.value = 'location'
  try {
    const { data } = await http.post('/locations/', { name, type: newLocationType.value })
    locations.value.push(data)
    locations.value.sort((a, b) => a.name.localeCompare(b.name, 'es'))
    newLocation.value = ''
    notify(`${LOCATION_TYPE_LABELS[data.type]} "${data.name}" creada`)
  } catch (e) {
    notify(errorMessage(e), 'error')
  } finally {
    savingNew.value = ''
  }
}

const locationTypeCount = computed(() => {
  const counts = { all: locations.value.length }
  for (const l of locations.value) counts[l.type] = (counts[l.type] ?? 0) + 1
  return counts
})

const filteredLocations = computed(() => {
  const q = locationSearch.value.trim().toLowerCase()
  return locations.value.filter(
    (l) =>
      (locationTypeFilter.value === 'all' || l.type === locationTypeFilter.value) &&
      (!q || l.name.toLowerCase().includes(q)),
  )
})

// Agrupadas por tipo (sucursales, CEDIS, corporativos) en el orden de LOCATION_TYPES
const locationGroups = computed(() =>
  LOCATION_TYPES.map((type) => ({
    type,
    items: filteredLocations.value.filter((l) => l.type === type),
  })).filter((g) => g.items.length),
)

function setLocationFilter(type) {
  locationTypeFilter.value = type
  if (type !== 'all') newLocationType.value = type
}

const categoryGroups = computed(() => notifyGroups.value.filter((g) => g.key !== ALWAYS_GROUP))

function groupName(key) {
  return notifyGroups.value.find((g) => g.key === key)?.name ?? key
}

async function changeNotifyGroup(item, group) {
  if (!group || group === item.notify_group) return
  try {
    const { data } = await http.put(`/incidencias/${item.id}`, { notify_group: group })
    replaceItem('incidencia', data)
    notify(`"${data.name}" ahora avisa al grupo ${groupName(data.notify_group)}`)
  } catch (e) {
    notify(errorMessage(e), 'error')
  }
}

function groupChanged(group) {
  return (groupDrafts.value[group.id] ?? []).join(',') !== group.emails.join(',')
}

async function saveGroup(group) {
  savingGroup.value = group.id
  try {
    const { data } = await http.put(`/notify-groups/${group.id}`, {
      emails: groupDrafts.value[group.id],
    })
    const i = notifyGroups.value.findIndex((g) => g.id === data.id)
    notifyGroups.value[i] = data
    groupDrafts.value[data.id] = [...data.emails]
    notify(`Grupo "${data.name}" actualizado`)
  } catch (e) {
    notify(errorMessage(e), 'error')
  } finally {
    savingGroup.value = null
  }
}

async function changeLocationType(item, type) {
  if (type === item.type) return
  try {
    const { data } = await http.put(`/locations/${item.id}`, { type })
    replaceItem('location', data)
    notify(`"${data.name}" ahora es ${LOCATION_TYPE_LABELS[data.type]}`)
  } catch (e) {
    notify(errorMessage(e), 'error')
  }
}

const KIND_URL = {
  incidencia: (id) => `/incidencias/${id}`,
  sub: (id) => `/incidencias/subincidencias/${id}`,
  location: (id) => `/locations/${id}`,
}
const KIND_TITLE = { incidencia: 'categoría', sub: 'subcategoría', location: 'ubicación' }

function urlFor(kind, item) {
  return KIND_URL[kind](item.id)
}

function replaceItem(kind, updated) {
  const list = { incidencia: incidencias, sub: subincidencias, location: locations }[kind]
  const i = list.value.findIndex((x) => x.id === updated.id)
  if (i >= 0) list.value[i] = updated
}

async function toggleActive(kind, item) {
  try {
    const { data } = await http.put(urlFor(kind, item), { is_active: !item.is_active })
    replaceItem(kind, data)
    notify(`"${data.name}" ${data.is_active ? 'activada' : 'desactivada'}`)
  } catch (e) {
    notify(errorMessage(e), 'error')
  }
}

function startEdit(kind, item) {
  editing.value = { kind, item, name: item.name }
}

async function saveEdit() {
  const { kind, item } = editing.value
  const name = editing.value.name.trim()
  if (name.length < 2) return
  if (name === item.name) {
    editing.value = null
    return
  }
  savingEdit.value = true
  try {
    const { data } = await http.put(urlFor(kind, item), { name })
    replaceItem(kind, data)
    editing.value = null
    notify('Nombre actualizado')
  } catch (e) {
    notify(errorMessage(e), 'error')
  } finally {
    savingEdit.value = false
  }
}
</script>

<template>
  <header class="d-flex flex-wrap align-center ga-3 mb-6">
    <div>
      <h2 class="text-h5">Catálogos</h2>
      <p class="text-body-2 text-secondary-label">
        Categorías y subcategorías que se eligen al crear un ticket
      </p>
    </div>
    <v-spacer />
    <v-btn icon="refresh-cw" variant="text" :loading="loading" title="Actualizar" @click="load" />
  </header>

  <v-alert v-if="error" type="error" class="mb-4">{{ error }}</v-alert>

  <v-alert type="info" density="compact" class="mb-6">
    Las categorías no se borran: se desactivan. Así los tickets que ya las usan las conservan,
    pero dejan de aparecer al crear uno nuevo.
  </v-alert>

  <v-row>
    <!-- Categorías -->
    <v-col cols="12" md="5">
      <v-card>
        <div class="pa-5 pb-3 font-weight-medium">Categorías</div>
        <form class="d-flex ga-2 px-5 pb-3" @submit.prevent="createIncidencia">
          <v-text-field
            v-model="newIncidencia"
            placeholder="Nueva categoría"
            hide-details
            density="compact"
            maxlength="100"
          />
          <v-btn
            type="submit"
            color="primary"
            icon="plus"
            :loading="savingNew === 'incidencia'"
            :disabled="newIncidencia.trim().length < 2"
            title="Agregar categoría"
          />
        </form>
        <v-divider />
        <v-list density="compact" class="pa-2">
          <v-list-item
            v-for="inc in incidencias"
            :key="inc.id"
            :active="inc.id === selectedId"
            color="primary"
            rounded="lg"
            @click="selectedId = inc.id"
          >
            <v-list-item-title :class="{ 'text-secondary-label': !inc.is_active }">
              {{ inc.name }}
            </v-list-item-title>
            <v-list-item-subtitle>
              {{ subCount[inc.id] ?? 0 }} subcategoría(s) ·
              {{ groupName(inc.notify_group) }}
              <span v-if="!inc.is_active"> · inactiva</span>
            </v-list-item-subtitle>
            <template #append>
              <v-btn
                icon="pencil"
                variant="text"
                size="x-small"
                title="Renombrar"
                @click.stop="startEdit('incidencia', inc)"
              />
              <v-switch
                :model-value="inc.is_active"
                color="primary"
                hide-details
                inset
                density="compact"
                :title="inc.is_active ? 'Desactivar' : 'Activar'"
                @click.stop
                @update:model-value="toggleActive('incidencia', inc)"
              />
            </template>
          </v-list-item>
          <p v-if="!incidencias.length && !loading" class="text-body-2 text-secondary-label pa-3">
            Aún no hay categorías.
          </p>
        </v-list>
      </v-card>
    </v-col>

    <!-- Subcategorías de la seleccionada -->
    <v-col cols="12" md="7">
      <v-card v-if="selected">
        <div class="pa-5 pb-3">
          <div class="text-caption text-secondary-label">Subcategorías de</div>
          <div class="font-weight-medium">{{ selected.name }}</div>
        </div>
        <div class="px-5 pb-4">
          <div class="d-flex flex-wrap align-center ga-3">
            <span class="text-body-2">Aviso por correo al grupo</span>
            <v-btn-toggle
              :model-value="selected.notify_group"
              color="primary"
              density="compact"
              variant="outlined"
              divided
              mandatory
              @update:model-value="changeNotifyGroup(selected, $event)"
            >
              <v-btn v-for="group in categoryGroups" :key="group.key" :value="group.key" size="small">
                {{ group.name }}
              </v-btn>
            </v-btn-toggle>
          </div>
          <div class="text-caption text-secondary-label mt-1">
            Ya asignado el ticket, los avisos van a este grupo, al técnico asignado y a quien lo levantó.
          </div>
        </div>
        <form class="d-flex ga-2 px-5 pb-3" @submit.prevent="createSub">
          <v-text-field
            v-model="newSub"
            placeholder="Nueva subcategoría"
            hide-details
            density="compact"
            maxlength="100"
          />
          <v-btn
            type="submit"
            color="primary"
            icon="plus"
            :loading="savingNew === 'sub'"
            :disabled="newSub.trim().length < 2"
            title="Agregar subcategoría"
          />
        </form>
        <v-divider />
        <v-list density="compact" class="pa-2">
          <v-list-item v-for="sub in subsOfSelected" :key="sub.id" rounded="lg">
            <v-list-item-title :class="{ 'text-secondary-label': !sub.is_active }">
              {{ sub.name }}
              <span v-if="!sub.is_active" class="text-caption"> · inactiva</span>
            </v-list-item-title>
            <template #append>
              <v-btn
                icon="pencil"
                variant="text"
                size="x-small"
                title="Renombrar"
                @click="startEdit('sub', sub)"
              />
              <v-switch
                :model-value="sub.is_active"
                color="primary"
                hide-details
                inset
                density="compact"
                :title="sub.is_active ? 'Desactivar' : 'Activar'"
                @update:model-value="toggleActive('sub', sub)"
              />
            </template>
          </v-list-item>
          <p v-if="!subsOfSelected.length" class="text-body-2 text-secondary-label pa-3">
            Esta categoría aún no tiene subcategorías. Sin al menos una activa, no se podrá elegir al crear un ticket.
          </p>
        </v-list>
      </v-card>
    </v-col>
  </v-row>

  <!-- Grupos de aviso por correo -->
  <v-card class="mt-6">
    <div class="pa-5 pb-3">
      <div class="font-weight-medium">Grupos de aviso por correo</div>
      <div class="text-caption text-secondary-label">
        Ticket nuevo: avisa a todos los grupos. Ya asignado: al grupo de su categoría y al técnico
        asignado. "Siempre en copia" va en todos. Escribe un correo y presiona Enter para agregarlo.
      </div>
    </div>
    <v-divider />
    <div class="pa-5 d-flex flex-column ga-4">
      <div v-for="group in notifyGroups" :key="group.id" class="d-flex flex-wrap align-center ga-3">
        <div class="group-name">{{ group.name }}</div>
        <v-combobox
          v-model="groupDrafts[group.id]"
          multiple
          chips
          closable-chips
          hide-details
          density="compact"
          placeholder="correo@empack.com.mx"
          class="group-emails"
        />
        <v-btn
          color="primary"
          variant="tonal"
          :loading="savingGroup === group.id"
          :disabled="!groupChanged(group)"
          @click="saveGroup(group)"
        >
          Guardar
        </v-btn>
      </div>
    </div>
  </v-card>

  <!-- Ubicaciones: sucursales, CEDIS y corporativos -->
  <v-card class="mt-6">
    <div class="d-flex flex-wrap align-center ga-3 pa-5 pb-3">
      <div>
        <div class="font-weight-medium">Ubicaciones</div>
        <div class="text-caption text-secondary-label">
          Se asignan a cada usuario; sus tickets se registran en automático con esa ubicación.
        </div>
      </div>
      <v-spacer />
      <v-text-field
        v-model="locationSearch"
        prepend-inner-icon="search"
        placeholder="Buscar"
        hide-details
        density="compact"
        clearable
        class="location-search"
      />
    </div>

    <div class="d-flex flex-wrap ga-2 px-5 pb-3">
      <v-chip
        :variant="locationTypeFilter === 'all' ? 'flat' : 'tonal'"
        :color="locationTypeFilter === 'all' ? 'primary' : undefined"
        @click="setLocationFilter('all')"
      >
        Todas · {{ locationTypeCount.all }}
      </v-chip>
      <v-chip
        v-for="type in LOCATION_TYPES"
        :key="type"
        :prepend-icon="LOCATION_TYPE_ICONS[type]"
        :variant="locationTypeFilter === type ? 'flat' : 'tonal'"
        :color="locationTypeFilter === type ? 'primary' : undefined"
        @click="setLocationFilter(type)"
      >
        {{ LOCATION_TYPE_PLURALS[type] }} · {{ locationTypeCount[type] ?? 0 }}
      </v-chip>
    </div>

    <form class="d-flex ga-2 px-5 pb-3" @submit.prevent="createLocation">
      <v-select
        v-model="newLocationType"
        :items="LOCATION_TYPES.map((t) => ({ value: t, title: LOCATION_TYPE_LABELS[t] }))"
        hide-details
        density="compact"
        class="location-type-select"
      />
      <v-text-field v-model="newLocation" placeholder="Nueva ubicación" hide-details density="compact" maxlength="150" />
      <v-btn
        type="submit"
        color="primary"
        icon="plus"
        :loading="savingNew === 'location'"
        :disabled="newLocation.trim().length < 2"
        title="Agregar ubicación"
      />
    </form>
    <v-divider />

    <div class="pa-2">
      <section v-for="group in locationGroups" :key="group.type" class="mb-2">
        <div class="location-group-title">
          {{ LOCATION_TYPE_PLURALS[group.type] }} · {{ group.items.length }}
        </div>
        <div class="location-grid">
          <div v-for="b in group.items" :key="b.id" class="location-item">
            <v-icon :icon="LOCATION_TYPE_ICONS[b.type]" size="16" class="text-secondary-label" />
            <span class="location-name" :class="{ 'text-secondary-label': !b.is_active }">
              {{ b.name }}<span v-if="!b.is_active" class="text-caption"> · inactiva</span>
            </span>
            <v-menu location="bottom end">
              <template #activator="{ props }">
                <v-btn v-bind="props" icon="ellipsis" variant="text" size="x-small" title="Cambiar tipo" />
              </template>
              <v-list density="compact" min-width="180">
                <v-list-subheader>Tipo de ubicación</v-list-subheader>
                <v-list-item
                  v-for="type in LOCATION_TYPES"
                  :key="type"
                  :prepend-icon="LOCATION_TYPE_ICONS[type]"
                  :title="LOCATION_TYPE_LABELS[type]"
                  :active="b.type === type"
                  color="primary"
                  @click="changeLocationType(b, type)"
                />
              </v-list>
            </v-menu>
            <v-btn icon="pencil" variant="text" size="x-small" title="Renombrar" @click="startEdit('location', b)" />
            <v-switch
              :model-value="b.is_active"
              color="primary"
              hide-details
              inset
              density="compact"
              :title="b.is_active ? 'Desactivar' : 'Activar'"
              @update:model-value="toggleActive('location', b)"
            />
          </div>
        </div>
      </section>
      <p v-if="!filteredLocations.length && !loading" class="text-body-2 text-secondary-label pa-3">
        {{ locations.length ? 'Ninguna ubicación coincide.' : 'Aún no hay ubicaciones.' }}
      </p>
    </div>
  </v-card>

  <v-dialog :model-value="!!editing" max-width="420" @update:model-value="editing = null">
    <v-card v-if="editing" class="pa-2">
      <v-card-title class="pt-4 px-5 text-h6">
        Renombrar {{ KIND_TITLE[editing.kind] }}
      </v-card-title>
      <v-card-text class="px-5">
        <form @submit.prevent="saveEdit">
          <v-text-field v-model="editing.name" autofocus maxlength="100" hide-details />
        </form>
      </v-card-text>
      <v-card-actions class="px-5 pb-4">
        <v-spacer />
        <v-btn variant="text" @click="editing = null">Cancelar</v-btn>
        <v-btn
          color="primary"
          :loading="savingEdit"
          :disabled="editing.name.trim().length < 2"
          @click="saveEdit"
        >
          Guardar
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <v-snackbar v-model="notice.show" :color="notice.color" timeout="4000" location="bottom right">
    {{ notice.text }}
  </v-snackbar>
</template>

<style scoped>
.location-search {
  max-width: 240px;
}
.group-name {
  flex: 0 0 140px;
  font-size: 14px;
  font-weight: 500;
}
.group-emails {
  flex: 1 1 320px;
}
.location-type-select {
  flex: 0 0 160px;
}
.location-group-title {
  padding: 10px 12px 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--app-text-secondary);
}
.location-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 0 8px;
}
.location-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 2px 8px 2px 12px;
  border-radius: 10px;
}
.location-item:hover {
  background: rgba(0, 0, 0, 0.03);
}
.location-name {
  flex: 1;
  min-width: 0;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
