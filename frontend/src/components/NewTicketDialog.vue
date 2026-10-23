<script setup>
import { nextTick, ref, watch } from 'vue'
import { errorMessage } from '../api/http'
import { catalogApi, ticketsApi } from '../api/tickets'
import { formatBytes } from '../utils/format'
import { MAX_TEXT } from '../utils/labels'
import FileDropzone from './FileDropzone.vue'

const open = defineModel({ type: Boolean, default: false })
const emit = defineEmits(['created'])

const form = ref(null)
const subSelect = ref(null)
const incidencias = ref([])
const subincidencias = ref([])
const incidenciaId = ref(null)
const subincidenciaId = ref(null)
const description = ref('')
const files = ref([])

const loadingCatalog = ref(false)
const loadingSubs = ref(false)
const saving = ref(false)
const progress = ref('')
const error = ref('')

const rules = {
  required: (v) => !!v || 'Campo obligatorio',
  minLength: (v) => (v ?? '').trim().length >= 5 || 'Describe el problema (mínimo 5 caracteres)',
}

function reset() {
  incidenciaId.value = null
  subincidenciaId.value = null
  subincidencias.value = []
  description.value = ''
  files.value = []
  error.value = ''
  progress.value = ''
  form.value?.resetValidation()
}

async function loadCatalog() {
  if (incidencias.value.length) return
  loadingCatalog.value = true
  try {
    incidencias.value = await catalogApi.incidencias()
  } catch (e) {
    error.value = errorMessage(e, 'No se pudo cargar el catálogo')
  } finally {
    loadingCatalog.value = false
  }
}

watch(open, (value) => {
  if (value) {
    reset()
    loadCatalog()
  }
})

watch(incidenciaId, async (id) => {
  subincidenciaId.value = null
  subincidencias.value = []
  // Al cambiar de categoría la subcategoría se vacía: sin esto se quedaba "Campo obligatorio"
  await nextTick()
  subSelect.value?.resetValidation()
  if (!id) return
  loadingSubs.value = true
  try {
    subincidencias.value = await catalogApi.subincidencias(id)
  } catch (e) {
    error.value = errorMessage(e, 'No se pudieron cargar las subcategorías')
  } finally {
    loadingSubs.value = false
  }
})

function addFiles(list) {
  files.value.push(...list)
}

function removeFile(index) {
  files.value.splice(index, 1)
}

async function submit() {
  const { valid } = await form.value.validate()
  if (!valid) return

  saving.value = true
  error.value = ''
  let ticket
  try {
    progress.value = 'Creando ticket…'
    ticket = await ticketsApi.create({
      incidencia_id: incidenciaId.value,
      subincidencia_id: subincidenciaId.value,
      description: description.value.trim(),
    })
  } catch (e) {
    error.value = errorMessage(e, 'No se pudo crear el ticket')
    saving.value = false
    progress.value = ''
    return
  }

  // El ticket ya existe: si algún adjunto falla, se avisa pero se continúa
  const failed = []
  for (const [i, file] of files.value.entries()) {
    progress.value = `Subiendo archivo ${i + 1} de ${files.value.length}…`
    try {
      await ticketsApi.uploadAttachment(ticket.id, file)
    } catch (e) {
      failed.push(`${file.name}: ${errorMessage(e)}`)
    }
  }

  saving.value = false
  progress.value = ''
  open.value = false
  emit('created', ticket, failed)
}
</script>

<template>
  <v-dialog v-model="open" max-width="600" :persistent="saving" scrollable>
    <v-card class="pa-2">
      <v-card-title class="d-flex align-center pt-4 px-5">
        <span class="text-h6">Nuevo ticket</span>
        <v-spacer />
        <v-btn icon="x" variant="text" size="small" :disabled="saving" @click="open = false" />
      </v-card-title>

      <v-card-text class="px-5">
        <v-alert v-if="error" type="error" density="compact" class="mb-4">{{ error }}</v-alert>

        <v-form ref="form" @submit.prevent="submit">
          <v-row dense>
            <v-col cols="12" sm="6">
              <label class="field-label">Categoría</label>
              <v-select
                v-model="incidenciaId"
                :items="incidencias"
                item-title="name"
                item-value="id"
                placeholder="Selecciona"
                :loading="loadingCatalog"
                :rules="[rules.required]"
                no-data-text="No hay categorías disponibles"
              />
            </v-col>
            <v-col cols="12" sm="6">
              <label class="field-label">Subcategoría</label>
              <v-select
                ref="subSelect"
                v-model="subincidenciaId"
                :items="subincidencias"
                item-title="name"
                item-value="id"
                :placeholder="incidenciaId ? 'Selecciona' : 'Elige primero la categoría'"
                :disabled="!incidenciaId"
                :loading="loadingSubs"
                :rules="[rules.required]"
                no-data-text="Esta categoría no tiene subcategorías"
              />
            </v-col>
          </v-row>

          <label class="field-label">Descripción</label>
          <v-textarea
            v-model="description"
            placeholder="¿Qué está pasando? Incluye lo que intentabas hacer y el mensaje de error si lo hay."
            rows="4"
            auto-grow
            :maxlength="MAX_TEXT"
            :counter="description.length > MAX_TEXT * 0.8 ? MAX_TEXT : undefined"
            :rules="[rules.minLength]"
          />

          <label class="field-label">Adjuntos (opcional)</label>
          <FileDropzone :paste="open" :disabled="saving" @files="addFiles" />

          <v-list v-if="files.length" density="compact" class="mt-2 pa-0 bg-transparent">
            <v-list-item
              v-for="(file, i) in files"
              :key="i"
              :title="file.name"
              :subtitle="formatBytes(file.size)"
              :prepend-icon="file.type.startsWith('image/') ? 'image' : 'paperclip'"
              rounded="lg"
            >
              <template #append>
                <v-btn icon="x" variant="text" size="x-small" :disabled="saving" @click="removeFile(i)" />
              </template>
            </v-list-item>
          </v-list>
        </v-form>

        <v-alert type="info" variant="tonal" density="compact" icon="info" class="mt-4 text-body-2">
          Cuando Soporte lo marque como resuelto, te pediremos confirmar la solución y calificar la atención.
          Si no respondes en 24 horas, se cerrará automáticamente con 5 estrellas.
        </v-alert>
      </v-card-text>

      <v-card-actions class="px-5 pb-4">
        <span class="text-body-2 text-secondary-label">{{ progress }}</span>
        <v-spacer />
        <v-btn variant="text" :disabled="saving" @click="open = false">Cancelar</v-btn>
        <v-btn color="primary" :loading="saving" @click="submit">Crear ticket</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
