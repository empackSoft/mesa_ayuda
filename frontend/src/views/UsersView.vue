<script setup>
import { computed, onMounted, ref } from 'vue'
import http, { errorMessage } from '../api/http'
import { locationsApi } from '../api/tickets'
import { useAuthStore } from '../stores/auth'
import { formatDate, initials } from '../utils/format'
import { LOCATION_TYPE_LABELS, ROLE_LABELS, label } from '../utils/labels'

// Administración de usuarios. Solo admin. No se borran: se desactivan.

const auth = useAuthStore()

const users = ref([])
const locations = ref([])
const locationName = computed(() => Object.fromEntries(locations.value.map((b) => [b.id, b.name])))
// Ordenadas por tipo (sucursales, CEDIS, corporativos) y nombre, con el tipo de subtítulo
const LOCATION_TYPE_ORDER = Object.keys(LOCATION_TYPE_LABELS)
const toLocationItem = (b) => ({ value: b.id, title: b.name, subtitle: label(LOCATION_TYPE_LABELS, b.type) })
const sortedLocations = computed(() =>
  [...locations.value].sort(
    (a, b) =>
      LOCATION_TYPE_ORDER.indexOf(a.type) - LOCATION_TYPE_ORDER.indexOf(b.type) ||
      a.name.localeCompare(b.name, 'es'),
  ),
)
// En el formulario: ubicaciones activas, más la actual del usuario aunque esté inactiva
const locationItems = computed(() =>
  sortedLocations.value.filter((b) => b.is_active || b.id === fields.value.location_id).map(toLocationItem),
)
// Los tickets toman la ubicación de quien los levanta: para un "user" es obligatoria
const locationRules = [(v) => fields.value.role !== 'user' || !!v || 'Obligatoria: sus tickets se registran con esta ubicación']
const loading = ref(false)
const error = ref('')
const notice = ref({ show: false, text: '', color: 'success' })

const search = ref('')
const roleFilter = ref(null)
const locationFilter = ref(null)
const showInactive = ref(false)

const dialog = ref(false)
const form = ref(null)
const editing = ref(null) // usuario que se edita; null = alta
const fields = ref({})
const showPassword = ref(false)
const saving = ref(false)
const formError = ref('')

const roleItems = Object.entries(ROLE_LABELS).map(([value, title]) => ({ value, title }))
const ROLE_COLORS = { user: 'grey', support: 'info', admin: 'primary' }

const rules = {
  required: (v) => !!(v ?? '').trim() || 'Campo obligatorio',
  name: (v) => (v ?? '').trim().length >= 2 || 'Mínimo 2 caracteres',
  email: (v) => /.+@.+\..+/.test(v ?? '') || 'Correo no válido',
  password: (v) => !v || v.length >= 6 || 'Mínimo 6 caracteres',
  passwordRequired: (v) => (v ?? '').length >= 6 || 'Mínimo 6 caracteres',
}

function notify(text, color = 'success') {
  notice.value = { show: true, text, color }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [{ data }, locationList] = await Promise.all([http.get('/users/'), locationsApi.list()])
    users.value = data
    locations.value = locationList
  } catch (e) {
    error.value = errorMessage(e, 'No se pudieron cargar los usuarios')
  } finally {
    loading.value = false
  }
}

onMounted(load)

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  return users.value.filter((u) => {
    if (!showInactive.value && !u.is_active) return false
    if (roleFilter.value && u.role !== roleFilter.value) return false
    if (locationFilter.value && u.location_id !== locationFilter.value) return false
    return !q || u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q)
  })
})

const inactiveCount = computed(() => users.value.filter((u) => !u.is_active).length)

const headers = [
  { title: 'Nombre', key: 'name' },
  { title: 'Ubicación', key: 'location_id', width: 200 },
  { title: 'Rol', key: 'role', width: 150 },
  { title: 'Estado', key: 'is_active', width: 120 },
  { title: 'Alta', key: 'created_at', width: 140 },
  { title: '', key: 'actions', sortable: false, width: 60, align: 'end' },
]

function isSelf(u) {
  return u.id === auth.user?.id
}

function openCreate() {
  editing.value = null
  fields.value = { name: '', email: '', role: 'user', location_id: null, password: '', is_active: true }
  formError.value = ''
  showPassword.value = false
  dialog.value = true
}

function openEdit(u) {
  editing.value = u
  fields.value = { name: u.name, email: u.email, role: u.role, location_id: u.location_id, password: '', is_active: u.is_active }
  formError.value = ''
  showPassword.value = false
  dialog.value = true
}

async function save() {
  const { valid } = await form.value.validate()
  if (!valid) return

  saving.value = true
  formError.value = ''
  const f = fields.value
  try {
    if (editing.value) {
      // Solo se mandan los campos que cambiaron
      const payload = {}
      if (f.name.trim() !== editing.value.name) payload.name = f.name.trim()
      if (f.email.trim() !== editing.value.email) payload.email = f.email.trim()
      if (f.role !== editing.value.role) payload.role = f.role
      if (f.location_id !== editing.value.location_id) payload.location_id = f.location_id
      if (f.is_active !== editing.value.is_active) payload.is_active = f.is_active
      if (f.password) payload.password = f.password
      if (Object.keys(payload).length) {
        const { data } = await http.put(`/users/${editing.value.id}`, payload)
        users.value = users.value.map((u) => (u.id === data.id ? data : u))
      }
      notify('Usuario actualizado')
    } else {
      const { data } = await http.post('/users/', {
        name: f.name.trim(),
        email: f.email.trim(),
        role: f.role,
        location_id: f.location_id,
        password: f.password,
      })
      users.value.unshift(data)
      notify(`Usuario ${data.name} creado`)
    }
    dialog.value = false
  } catch (e) {
    formError.value = errorMessage(e, 'No se pudo guardar el usuario')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <header class="d-flex flex-wrap align-center ga-3 mb-6">
    <div>
      <h2 class="text-h5">Usuarios</h2>
      <p class="text-body-2 text-secondary-label">Cuentas, roles y accesos</p>
    </div>
    <v-spacer />
    <v-btn icon="refresh-cw" variant="text" :loading="loading" title="Actualizar" @click="load" />
    <v-btn color="primary" prepend-icon="user-plus" @click="openCreate">Nuevo usuario</v-btn>
  </header>

  <v-alert v-if="error" type="error" class="mb-4">{{ error }}</v-alert>

  <v-card>
    <div class="d-flex flex-wrap ga-3 pa-4">
      <v-text-field
        v-model="search"
        prepend-inner-icon="search"
        placeholder="Buscar por nombre o correo"
        hide-details
        clearable
        class="filter-search"
      />
      <v-select
        v-model="roleFilter"
        :items="roleItems"
        placeholder="Rol"
        hide-details
        clearable
        class="filter-role"
      />
      <v-autocomplete
        v-model="locationFilter"
        :items="sortedLocations.map(toLocationItem)"
        item-props
        placeholder="Ubicación"
        hide-details
        clearable
        class="filter-location"
      />
      <v-switch
        v-model="showInactive"
        :label="`Mostrar inactivos (${inactiveCount})`"
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
      :items-per-page="25"
      :sort-by="[{ key: 'name', order: 'asc' }]"
      hover
    >
      <template #item.name="{ item }">
        <div class="d-flex align-center ga-3 py-2">
          <v-avatar :color="item.is_active ? 'primary' : 'grey'" size="32">
            <span class="avatar-initials">{{ initials(item.name) }}</span>
          </v-avatar>
          <div>
            <div class="font-weight-medium" :class="{ 'text-secondary-label': !item.is_active }">
              {{ item.name }}
              <span v-if="isSelf(item)" class="text-caption text-secondary-label">(tú)</span>
            </div>
            <div class="text-body-2 text-secondary-label">{{ item.email }}</div>
          </div>
        </div>
      </template>

      <template #item.location_id="{ item }">
        <span v-if="item.location_id" class="text-body-2">{{ locationName[item.location_id] }}</span>
        <span v-else class="text-body-2 text-secondary-label">—</span>
      </template>

      <template #item.role="{ item }">
        <v-chip :color="ROLE_COLORS[item.role]">{{ label(ROLE_LABELS, item.role) }}</v-chip>
      </template>

      <template #item.is_active="{ item }">
        <span v-if="item.is_active" class="d-inline-flex align-center ga-1 text-body-2">
          <v-icon icon="circle-check" size="14" color="success" /> Activo
        </span>
        <span v-else class="d-inline-flex align-center ga-1 text-body-2 text-secondary-label">
          <v-icon icon="circle-x" size="14" /> Inactivo
        </span>
      </template>

      <template #item.created_at="{ item }">
        <span class="text-body-2">{{ formatDate(item.created_at) }}</span>
      </template>

      <template #item.actions="{ item }">
        <v-btn icon="pencil" variant="text" size="small" title="Editar" @click="openEdit(item)" />
      </template>

      <template #no-data>
        <v-empty-state icon="users" title="Sin resultados" text="Ningún usuario coincide con los filtros." size="56" />
      </template>
    </v-data-table>
  </v-card>

  <v-dialog v-model="dialog" max-width="520" :persistent="saving">
    <v-card class="pa-2">
      <v-card-title class="d-flex align-center pt-4 px-5">
        <span class="text-h6">{{ editing ? 'Editar usuario' : 'Nuevo usuario' }}</span>
        <v-spacer />
        <v-btn icon="x" variant="text" size="small" :disabled="saving" @click="dialog = false" />
      </v-card-title>

      <v-card-text class="px-5">
        <v-alert v-if="formError" type="error" density="compact" class="mb-4">{{ formError }}</v-alert>

        <v-form ref="form" @submit.prevent="save">
          <label class="field-label">Nombre completo</label>
          <v-text-field v-model="fields.name" :rules="[rules.name]" maxlength="150" class="mb-1" />

          <label class="field-label">Correo</label>
          <v-text-field
            v-model="fields.email"
            type="email"
            :rules="[rules.email]"
            maxlength="150"
            autocomplete="off"
            class="mb-1"
          />

          <label class="field-label">Ubicación</label>
          <v-autocomplete
            v-model="fields.location_id"
            :items="locationItems"
            item-props
            :rules="locationRules"
            placeholder="Sin ubicación"
            clearable
            hint="Sus tickets se registran en automático con esta ubicación."
            persistent-hint
            class="mb-3"
          />

          <label class="field-label">Rol</label>
          <v-select
            v-model="fields.role"
            :items="roleItems"
            :disabled="editing && isSelf(editing)"
            :hint="editing && isSelf(editing) ? 'No puedes cambiar tu propio rol' : ''"
            persistent-hint
            class="mb-3"
          />

          <label class="field-label">{{ editing ? 'Nueva contraseña (opcional)' : 'Contraseña' }}</label>
          <v-text-field
            v-model="fields.password"
            :type="showPassword ? 'text' : 'password'"
            :append-inner-icon="showPassword ? 'eye-off' : 'eye'"
            :rules="[editing ? rules.password : rules.passwordRequired]"
            :placeholder="editing ? 'Déjala vacía para no cambiarla' : ''"
            hint="Mínimo 6 caracteres."
            persistent-hint
            autocomplete="new-password"
            class="mb-3"
            @click:append-inner="showPassword = !showPassword"
          />

          <v-switch
            v-if="editing"
            v-model="fields.is_active"
            color="primary"
            inset
            hide-details
            :disabled="isSelf(editing)"
            :label="fields.is_active ? 'Cuenta activa' : 'Cuenta inactiva (no puede iniciar sesión)'"
          />
          <p v-if="editing && isSelf(editing)" class="text-caption text-secondary-label">
            No puedes desactivar tu propia cuenta.
          </p>
        </v-form>
      </v-card-text>

      <v-card-actions class="px-5 pb-4">
        <v-spacer />
        <v-btn variant="text" :disabled="saving" @click="dialog = false">Cancelar</v-btn>
        <v-btn color="primary" :loading="saving" @click="save">
          {{ editing ? 'Guardar cambios' : 'Crear usuario' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <v-snackbar v-model="notice.show" :color="notice.color" timeout="4000" location="bottom right">
    {{ notice.text }}
  </v-snackbar>
</template>

<style scoped>
.filter-search {
  flex: 1 1 280px;
}
.filter-role {
  flex: 0 1 180px;
}
.filter-location {
  flex: 0 1 220px;
}
.avatar-initials {
  font-size: 12px;
  font-weight: 600;
}
</style>
