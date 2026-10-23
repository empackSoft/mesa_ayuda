<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { notificationsApi } from '../api/tickets'
import { useFeedbackStore } from '../stores/feedback'
import { timeAgo, formatDateTime } from '../utils/format'
import {
  isMuted, needsActivation, playSound, requestSystemPermission, setMuted, showSystemNotification,
  systemPermission,
} from '../utils/alerts'
import { flashTab, setUnreadBadge } from '../utils/tabBadge'
import NotificationToasts from './NotificationToasts.vue'

// Campanita: revisa avisos cada 15 s. Con cada aviso nuevo suena, aparece una tarjeta
// abajo a la derecha (30 s) y, si la pestaña está oculta, una notificación del sistema
// y el título de la pestaña parpadea. Mientras haya sin leer, la pestaña muestra el contador.
const POLL_MS = 15000
const TOAST_MS = 30000
const MAX_TOASTS = 3

const router = useRouter()
const feedback = useFeedbackStore()

const items = ref([])
const unread = ref(0)
const open = ref(false)
const muted = ref(isMuted())

const toasts = ref([])
const askActivation = ref(false)
const activationSkipped = ref(false)

let pollTimer = null
let lastSeenId = null
const toastTimers = new Map()

function toggleMute() {
  muted.value = !muted.value
  setMuted(muted.value)
  if (!muted.value) playSound('ticket_update')
}

// --- Tarjetas emergentes ---
function startToastTimer(toast, ms = TOAST_MS) {
  clearTimeout(toastTimers.get(toast.id))
  toast.expiresAt = Date.now() + ms
  toastTimers.set(toast.id, setTimeout(() => dismissToast(toast), ms))
}

function pauseToast(toast) {
  clearTimeout(toastTimers.get(toast.id))
  toast.remaining = Math.max(toast.expiresAt - Date.now(), 3000)
}

function resumeToast(toast) {
  startToastTimer(toast, toast.remaining ?? TOAST_MS)
}

function dismissToast(toast) {
  clearTimeout(toastTimers.get(toast.id))
  toastTimers.delete(toast.id)
  toasts.value = toasts.value.filter((t) => t.id !== toast.id)
}

function clearToasts() {
  toasts.value.forEach((t) => clearTimeout(toastTimers.get(t.id)))
  toastTimers.clear()
  toasts.value = []
}

function showToasts(newOnes) {
  for (const n of [...newOnes].reverse()) {
    const toast = { ...n }
    toasts.value = [toast, ...toasts.value]
    startToastTimer(toast)
  }
  // Se quedan solo las más recientes
  toasts.value.slice(MAX_TOASTS).forEach(dismissToast)
}

function onToastClick() {
  clearToasts()
  open.value = true
}

// --- Permisos (sonido y notificaciones del navegador) ---
async function activate() {
  askActivation.value = false
  // Este clic ya cuenta como interacción: desbloquea el audio y se escucha de prueba
  await requestSystemPermission()
  if (!muted.value) playSound('ticket_update')
}

function skipActivation() {
  askActivation.value = false
  activationSkipped.value = true
}

async function announce(newOnes) {
  const newest = newOnes[0]
  if (!muted.value) {
    const played = await playSound(newOnes.some((n) => n.kind === 'new_ticket') ? 'new_ticket' : newest.kind)
    if (!played && !activationSkipped.value) askActivation.value = true
  }
  // Primer aviso: se pide el permiso de notificaciones (si el navegador lo permite sin clic,
  // aparece su ventana; si no, queda el botón "Activar" en la tarjeta)
  if (systemPermission() === 'default') {
    requestSystemPermission()
    if (!activationSkipped.value) askActivation.value = needsActivation()
  }
  newOnes.forEach((n) => showSystemNotification(n, () => goTo(n)))
  flashTab()
}

async function poll() {
  try {
    const data = await notificationsApi.list()
    const newOnes = lastSeenId === null ? [] : data.items.filter((n) => n.id > lastSeenId && !n.is_read)
    lastSeenId = Math.max(lastSeenId ?? 0, data.items[0]?.id ?? 0)
    items.value = data.items
    unread.value = data.unread_count
    if (newOnes.length) {
      showToasts(newOnes)
      announce(newOnes)
      // Un aviso nuevo puede ser "tu ticket fue resuelto": se revisa la encuesta pendiente
      feedback.refresh()
    }
  } catch {
    // sin conexión o sesión vencida: se reintenta en el siguiente ciclo
  }
}

function goTo(n) {
  if (!n.is_read) {
    n.is_read = true
    unread.value = Math.max(0, unread.value - 1)
    notificationsApi.markRead(n.id).catch(() => {})
  }
  if (n.ticket_id) router.push({ name: 'ticket-detail', params: { id: n.ticket_id } })
}

function openNotification(n) {
  open.value = false
  const item = items.value.find((i) => i.id === n.id) ?? n
  goTo(item)
}

async function markAll() {
  items.value.forEach((n) => (n.is_read = true))
  unread.value = 0
  await notificationsApi.markAllRead().catch(() => {})
}

watch(unread, setUnreadBadge)

onMounted(() => {
  poll()
  pollTimer = setInterval(poll, POLL_MS)
})

onBeforeUnmount(() => {
  clearInterval(pollTimer)
  clearToasts()
  setUnreadBadge(0)
})
</script>

<template>
  <v-menu v-model="open" location="bottom end" :close-on-content-click="false">
    <template #activator="{ props }">
      <v-btn v-bind="props" icon variant="text" class="mr-1" :title="unread ? `${unread} aviso(s) sin leer` : 'Avisos'">
        <v-icon icon="bell" size="20" />
        <!-- Contador dentro del botón: un v-badge flotante se salía y la barra superior lo recortaba -->
        <span v-if="unread" class="bell-count">{{ unread > 99 ? '99+' : unread }}</span>
      </v-btn>
    </template>

    <v-card width="360" max-width="calc(100vw - 24px)" class="pa-2">
      <div class="d-flex align-center px-3 pt-2 pb-2">
        <span class="font-weight-medium">Avisos</span>
        <v-spacer />
        <v-btn
          :icon="muted ? 'volume-x' : 'volume-2'"
          variant="text"
          size="small"
          :title="muted ? 'Activar sonido' : 'Silenciar'"
          @click="toggleMute"
        />
        <v-btn
          icon="check-check"
          variant="text"
          size="small"
          title="Marcar todos como leídos"
          :disabled="!unread"
          @click="markAll"
        />
      </div>
      <v-divider />

      <div v-if="!items.length" class="text-center text-body-2 text-secondary-label py-8">
        <v-icon icon="bell-off" size="28" class="mb-2" /><br />
        No tienes avisos
      </div>

      <v-list v-else density="compact" class="py-1 list">
        <v-list-item
          v-for="n in items"
          :key="n.id"
          rounded="lg"
          class="mb-1"
          :class="{ unread: !n.is_read }"
          @click="openNotification(n)"
        >
          <div class="d-flex ga-2">
            <span class="dot" :class="{ 'dot--on': !n.is_read }" />
            <div class="min-w-0">
              <div class="text-body-2 font-weight-medium">{{ n.title }}</div>
              <div v-if="n.body" class="text-caption text-secondary-label body">{{ n.body }}</div>
              <div class="text-caption text-secondary-label" :title="formatDateTime(n.created_at)">
                {{ timeAgo(n.created_at) }}
              </div>
            </div>
          </div>
        </v-list-item>
      </v-list>
    </v-card>
  </v-menu>

  <NotificationToasts
    :toasts="toasts"
    :ask-activation="askActivation"
    @open="onToastClick"
    @dismiss="dismissToast"
    @pause="pauseToast"
    @resume="resumeToast"
    @activate="activate"
    @skip-activation="skipActivation"
  />
</template>

<style scoped>
.bell-count {
  position: absolute;
  top: 4px;
  right: 2px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: rgb(var(--v-theme-error));
  color: rgb(var(--v-theme-on-error));
  font-size: 11px;
  font-weight: 600;
  line-height: 18px;
  text-align: center;
  box-shadow: 0 0 0 2px rgb(var(--v-theme-surface));
  pointer-events: none;
}
.list {
  max-height: 420px;
  overflow-y: auto;
}
.unread {
  background: rgba(11, 40, 121, 0.05);
}
.dot {
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  margin-top: 6px;
  border-radius: 50%;
  background: transparent;
}
.dot--on {
  background: rgb(var(--v-theme-primary));
}
.min-w-0 {
  min-width: 0;
}
.body {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
