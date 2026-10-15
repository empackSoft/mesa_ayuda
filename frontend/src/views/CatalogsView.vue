<script setup>
import { computed, onMounted, ref } from 'vue'
import http, { errorMessage } from '../api/http'

// Catálogo de incidencias (categorías) y subincidencias (subcategorías). Solo admin.
// No se borra nada: se desactiva, para no romper tickets que ya las usan.

const incidencias = ref([])
const subincidencias = ref([])
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
    const [inc, subs] = await Promise.all([
      http.get('/incidencias/').then((r) => r.data),
      http.get('/incidencias/subincidencias/all').then((r) => r.data),
    ])
    incidencias.value = inc
    subincidencias.value = subs
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

function urlFor(kind, item) {
  return kind === 'incidencia' ? `/incidencias/${item.id}` : `/incidencias/subincidencias/${item.id}`
}

function replaceItem(kind, updated) {
  const list = kind === 'incidencia' ? incidencias : subincidencias
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
              {{ subCount[inc.id] ?? 0 }} subcategoría(s)
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

  <v-dialog :model-value="!!editing" max-width="420" @update:model-value="editing = null">
    <v-card v-if="editing" class="pa-2">
      <v-card-title class="pt-4 px-5 text-h6">
        Renombrar {{ editing.kind === 'incidencia' ? 'categoría' : 'subcategoría' }}
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
