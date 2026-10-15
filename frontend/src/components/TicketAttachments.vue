<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
import { errorMessage } from '../api/http'
import { ticketsApi } from '../api/tickets'
import { formatDateTime } from '../utils/format'
import FileDropzone from './FileDropzone.vue'

const props = defineProps({
  ticketId: { type: [Number, String], required: true },
  closed: { type: Boolean, default: false },
})

const emit = defineEmits(['uploaded'])

const attachments = ref([])
const previews = ref({}) // id de adjunto -> object URL de la miniatura
const loading = ref(false)
const uploading = ref('')
const error = ref('')
const preview = ref(null)

const IMAGE_EXT = ['.png', '.jpg', '.jpeg']

function nameOf(a) {
  return a.original_name || a.file_path.split('/').pop()
}

function isImage(a) {
  return IMAGE_EXT.some((ext) => nameOf(a).toLowerCase().endsWith(ext))
}

function iconOf(a) {
  const name = nameOf(a).toLowerCase()
  if (name.endsWith('.zip')) return 'file-archive'
  if (/\.(xlsx?)$/.test(name)) return 'file-spreadsheet'
  if (/\.(pdf|docx?|txt)$/.test(name)) return 'file-text'
  return 'file'
}

function revokePreviews() {
  Object.values(previews.value).forEach((url) => URL.revokeObjectURL(url))
  previews.value = {}
}

// Las miniaturas se piden con el token (la descarga no es pública)
async function loadPreviews() {
  for (const a of attachments.value.filter(isImage)) {
    if (previews.value[a.id]) continue
    try {
      const blob = await ticketsApi.downloadAttachment(props.ticketId, a.id)
      previews.value = { ...previews.value, [a.id]: URL.createObjectURL(blob) }
    } catch {
      // sin miniatura: se muestra el icono genérico
    }
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    attachments.value = await ticketsApi.attachments(props.ticketId)
    loadPreviews()
  } catch (e) {
    error.value = errorMessage(e, 'No se pudieron cargar los adjuntos')
  } finally {
    loading.value = false
  }
}

async function upload(files) {
  error.value = ''
  const failed = []
  for (const [i, file] of files.entries()) {
    uploading.value = files.length > 1 ? `Subiendo ${i + 1} de ${files.length}…` : `Subiendo ${file.name}…`
    try {
      await ticketsApi.uploadAttachment(props.ticketId, file)
    } catch (e) {
      failed.push(`${file.name}: ${errorMessage(e)}`)
    }
  }
  uploading.value = ''
  if (failed.length) error.value = failed.join(' · ')
  await load()
  emit('uploaded')
}

async function download(a) {
  try {
    const blob = await ticketsApi.downloadAttachment(props.ticketId, a.id)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = nameOf(a)
    link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch (e) {
    error.value = errorMessage(e, 'No se pudo descargar el archivo')
  }
}

function open(a) {
  if (previews.value[a.id]) preview.value = a
  else download(a)
}

watch(() => props.ticketId, () => {
  revokePreviews()
  load()
}, { immediate: true })

onBeforeUnmount(revokePreviews)
</script>

<template>
  <v-card class="pa-5">
    <div class="d-flex align-center mb-3">
      <v-icon icon="paperclip" size="18" class="mr-2 text-secondary-label" />
      <span class="font-weight-medium">Adjuntos</span>
      <span v-if="attachments.length" class="ml-2 text-secondary-label">{{ attachments.length }}</span>
    </div>

    <v-alert v-if="error" type="error" density="compact" class="mb-3" closable @click:close="error = ''">
      {{ error }}
    </v-alert>

    <v-progress-linear v-if="loading && !attachments.length" indeterminate color="primary" class="mb-3" />

    <div v-if="attachments.length" class="attachment-list mb-3">
      <button
        v-for="a in attachments"
        :key="a.id"
        type="button"
        class="attachment"
        :title="`${nameOf(a)} · ${formatDateTime(a.created_at)}`"
        @click="open(a)"
      >
        <img v-if="previews[a.id]" :src="previews[a.id]" :alt="nameOf(a)" class="thumb">
        <span v-else class="thumb thumb--icon"><v-icon :icon="iconOf(a)" size="22" /></span>
        <span class="attachment-name text-body-2">{{ nameOf(a) }}</span>
        <v-icon icon="download" size="16" class="text-secondary-label" @click.stop="download(a)" />
      </button>
    </div>

    <p v-else-if="!loading" class="text-body-2 text-secondary-label mb-3">Sin archivos adjuntos.</p>

    <template v-if="!closed">
      <FileDropzone compact :disabled="!!uploading" @files="upload" />
      <div class="text-caption text-secondary-label mt-2">
        <template v-if="uploading">{{ uploading }}</template>
        <template v-else>Puedes pegar capturas con Ctrl+V en cualquier parte de esta página.</template>
      </div>
    </template>
    <p v-else class="text-caption text-secondary-label">El ticket está cerrado; ya no admite archivos.</p>

    <v-dialog :model-value="!!preview" max-width="1000" @update:model-value="preview = null">
      <v-card v-if="preview" class="pa-3">
        <div class="d-flex align-center mb-2 px-1">
          <span class="text-body-2 font-weight-medium text-truncate">{{ nameOf(preview) }}</span>
          <v-spacer />
          <v-btn icon="download" variant="text" size="small" @click="download(preview)" />
          <v-btn icon="x" variant="text" size="small" @click="preview = null" />
        </div>
        <img :src="previews[preview.id]" :alt="nameOf(preview)" class="preview-img">
      </v-card>
    </v-dialog>
  </v-card>
</template>

<style scoped>
.attachment-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.attachment {
  border: none;
  background: none;
  font: inherit;
  color: inherit;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 8px;
  border-radius: 10px;
  text-align: left;
  width: 100%;
  transition: background 0.15s ease;
}
.attachment:hover {
  background: rgba(0, 0, 0, 0.04);
}
.thumb {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  object-fit: cover;
  flex-shrink: 0;
  border: 1px solid var(--app-hairline);
}
.thumb--icon {
  display: grid;
  place-items: center;
  background: rgba(11, 40, 121, 0.06);
  color: rgb(var(--v-theme-primary));
  border: none;
}
.attachment-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.preview-img {
  display: block;
  max-width: 100%;
  max-height: 75vh;
  margin: 0 auto;
  border-radius: 8px;
}
</style>
