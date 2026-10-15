<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { ALLOWED_EXTENSIONS, MAX_FILE_SIZE } from '../utils/labels'
import { formatBytes } from '../utils/format'

// Zona para soltar archivos, elegirlos o pegarlos con Ctrl+V.
// Solo valida y emite "files" con los archivos válidos; el padre decide qué hacer.
const props = defineProps({
  disabled: { type: Boolean, default: false },
  // Escuchar Ctrl+V en toda la página (solo una zona activa a la vez)
  paste: { type: Boolean, default: true },
  compact: { type: Boolean, default: false },
})

const emit = defineEmits(['files'])

const input = ref(null)
const dragging = ref(false)
const errors = ref([])
let dragDepth = 0

function extensionOf(name) {
  const i = name.lastIndexOf('.')
  return i >= 0 ? name.slice(i).toLowerCase() : ''
}

// Las capturas pegadas llegan como "image.png"; se les da un nombre con fecha
function nameForPasted(file) {
  const ext = file.type === 'image/jpeg' ? '.jpg' : '.png'
  const stamp = new Date().toISOString().slice(0, 19).replace(/[-:T]/g, '')
  return new File([file], `captura-${stamp}${ext}`, { type: file.type })
}

function accept(fileList, pasted = false) {
  if (props.disabled) return
  const valid = []
  const problems = []
  for (let file of fileList) {
    if (pasted) file = nameForPasted(file)
    if (!ALLOWED_EXTENSIONS.includes(extensionOf(file.name))) {
      problems.push(`${file.name}: tipo de archivo no permitido`)
    } else if (file.size === 0) {
      problems.push(`${file.name}: el archivo está vacío`)
    } else if (file.size > MAX_FILE_SIZE) {
      problems.push(`${file.name}: pesa ${formatBytes(file.size)} (máximo ${formatBytes(MAX_FILE_SIZE)})`)
    } else {
      valid.push(file)
    }
  }
  errors.value = problems
  if (valid.length) emit('files', valid)
}

function onDragEnter() {
  dragDepth++
  dragging.value = true
}

function onDragLeave() {
  dragDepth = Math.max(0, dragDepth - 1)
  if (dragDepth === 0) dragging.value = false
}

function onDrop(e) {
  dragDepth = 0
  dragging.value = false
  accept(e.dataTransfer?.files ?? [])
}

function onPick(e) {
  accept(e.target.files ?? [])
  e.target.value = ''
}

// Solo intercepta el pegado si trae archivos; el texto pegado sigue normal
function onPaste(e) {
  if (!props.paste || props.disabled) return
  const files = [...(e.clipboardData?.files ?? [])]
  if (!files.length) return
  e.preventDefault()
  const onlyImages = files.every((f) => f.type.startsWith('image/'))
  accept(files, onlyImages)
}

onMounted(() => document.addEventListener('paste', onPaste))
onBeforeUnmount(() => document.removeEventListener('paste', onPaste))
</script>

<template>
  <div>
    <div
      class="dropzone"
      :class="{ 'dropzone--active': dragging, 'dropzone--disabled': disabled, 'dropzone--compact': compact }"
      role="button"
      tabindex="0"
      @click="!disabled && input.click()"
      @keydown.enter.prevent="!disabled && input.click()"
      @dragenter.prevent="onDragEnter"
      @dragover.prevent
      @dragleave.prevent="onDragLeave"
      @drop.prevent="onDrop"
    >
      <v-icon icon="upload" size="20" class="mb-1" />
      <div class="text-body-2">
        <span class="text-primary font-weight-medium">Elige archivos</span>
        o arrástralos aquí
      </div>
      <div v-if="!compact" class="text-caption text-secondary-label mt-1">
        <v-icon icon="clipboard-paste" size="12" /> También puedes pegar una captura con Ctrl+V ·
        Máx. 10 MB
      </div>
      <input
        ref="input"
        type="file"
        multiple
        hidden
        :accept="ALLOWED_EXTENSIONS.join(',')"
        @change="onPick"
      >
    </div>

    <v-alert
      v-if="errors.length"
      type="warning"
      density="compact"
      class="mt-2"
      closable
      @click:close="errors = []"
    >
      <div v-for="msg in errors" :key="msg" class="text-body-2">{{ msg }}</div>
    </v-alert>
  </div>
</template>

<style scoped>
.dropzone {
  border: 1.5px dashed rgba(0, 0, 0, 0.16);
  border-radius: 14px;
  padding: 18px 16px;
  text-align: center;
  cursor: pointer;
  color: var(--app-text-secondary);
  transition: background 0.15s ease, border-color 0.15s ease;
}
.dropzone:hover,
.dropzone:focus-visible {
  background: rgba(0, 0, 0, 0.02);
  outline: none;
}
.dropzone--compact {
  padding: 12px;
}
.dropzone--active {
  border-color: rgb(var(--v-theme-primary));
  background: rgba(11, 40, 121, 0.05);
}
.dropzone--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
