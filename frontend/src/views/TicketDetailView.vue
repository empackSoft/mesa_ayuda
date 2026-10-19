<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { errorMessage } from '../api/http'
import { ticketsApi, usersApi } from '../api/tickets'
import MascotPeek from '../components/MascotPeek.vue'
import TicketAttachments from '../components/TicketAttachments.vue'
import TicketConversation from '../components/TicketConversation.vue'
import TicketFeedback from '../components/TicketFeedback.vue'
import { useAuthStore } from '../stores/auth'
import { useFeedbackStore } from '../stores/feedback'
import { formatDateTime, timeAgo } from '../utils/format'
import {
  PRIORITY_COLORS, PRIORITY_LABELS, RATING_LABELS, STATUS_COLORS, STATUS_LABELS, STATUS_TRANSITIONS,
  historyText, isFinal, label,
} from '../utils/labels'

const route = useRoute()
const auth = useAuthStore()
const feedback = useFeedbackStore()
const conversation = ref(null)

const ticket = ref(null)
const history = ref([])
const staff = ref([])
const loading = ref(false)
const loadError = ref('')
const notFound = ref(false)
const busy = ref('') // acción en curso: 'assign', 'status', 'priority', 'close', 'cancel'
const confirmClose = ref(false)
const cancelDialog = ref(false)
const cancelReason = ref('')
const notice = ref({ show: false, text: '', color: 'success' })

const ticketId = computed(() => route.params.id)
const closed = computed(() => isFinal(ticket.value?.status))

const isOwner = computed(() => ticket.value?.created_by_user_id === auth.user?.id)

// Mismas reglas que CANCELLABLE_STATUSES / ensure_ticket_access en ticketService.py
const canCancel = computed(
  () => ['open', 'in_progress', 'pending'].includes(ticket.value?.status) && (auth.isStaff || isOwner.value),
)

const staffById = computed(() => Object.fromEntries(staff.value.map((u) => [String(u.id), u.name])))

// "Cerrar" usa su propio endpoint; aquí solo los demás pasos del flujo
const nextStatuses = computed(() =>
  (STATUS_TRANSITIONS[ticket.value?.status] ?? []).filter((s) => s !== 'closed'),
)

const priorityItems = Object.entries(PRIORITY_LABELS).map(([value, title]) => ({ value, title }))

function notify(text, color = 'success') {
  notice.value = { show: true, text, color }
}

async function loadHistory() {
  if (!auth.isStaff) return
  try {
    history.value = await ticketsApi.history(ticketId.value)
  } catch {
    history.value = []
  }
}

async function load() {
  loading.value = true
  loadError.value = ''
  notFound.value = false
  try {
    ticket.value = await ticketsApi.get(ticketId.value)
    loadHistory()
  } catch (e) {
    ticket.value = null
    const status = e.response?.status
    if (status === 404 || status === 403 || status === 422) notFound.value = true
    else loadError.value = errorMessage(e, 'No se pudo cargar el ticket')
  } finally {
    loading.value = false
  }
}

async function loadStaff() {
  if (!auth.isStaff) return
  try {
    staff.value = await usersApi.staff()
  } catch {
    staff.value = []
  }
}

// Ejecuta una acción de soporte y refresca ticket + historial
async function run(kind, action, successText) {
  busy.value = kind
  try {
    ticket.value = await action()
    notify(successText)
    loadHistory()
  } catch (e) {
    notify(errorMessage(e), 'error')
  } finally {
    busy.value = ''
  }
}

function assignTo(userId) {
  if (!userId || userId === ticket.value.assigned_to_user_id) return
  const name = staff.value.find((u) => u.id === userId)?.name ?? 'el técnico'
  run('assign', () => ticketsApi.assign(ticket.value.id, userId), `Ticket asignado a ${name}`)
}

function changeStatus(status) {
  run(
    'status',
    () => ticketsApi.changeStatus(ticket.value.id, status),
    `Estado cambiado a ${label(STATUS_LABELS, status)}`,
  )
}

function changePriority(priority) {
  if (!priority || priority === ticket.value.priority) return
  run(
    'priority',
    () => ticketsApi.update(ticket.value.id, { priority }),
    `Prioridad cambiada a ${label(PRIORITY_LABELS, priority)}`,
  )
}

async function closeTicket() {
  confirmClose.value = false
  await run('close', () => ticketsApi.close(ticket.value.id), 'Ticket cerrado')
}

function openCancel() {
  cancelReason.value = ''
  cancelDialog.value = true
}

async function cancelTicket() {
  if (cancelReason.value.trim().length < 5) return
  cancelDialog.value = false
  await run('cancel', () => ticketsApi.cancel(ticket.value.id, cancelReason.value.trim()), 'Ticket cancelado')
}

function onAnswered(updated, kind) {
  ticket.value = updated
  feedback.remove(updated.id)
  notify(kind === 'reopen' ? 'Reabrimos el ticket. Soporte ya fue notificado.' : '¡Gracias! Registramos tu calificación.')
  loadHistory()
  // Al reabrir, el motivo se agrega a la conversación
  if (kind === 'reopen') conversation.value?.load()
}

onMounted(() => {
  // Aviso que deja la pantalla anterior (ej. "Ticket creado")
  const pending = window.history.state?.notice
  if (pending) notify(pending.text, pending.color)
  loadStaff()
})

watch(ticketId, load, { immediate: true })
</script>

<template>
  <v-btn
    :to="{ name: 'tickets' }"
    variant="text"
    prepend-icon="arrow-left"
    class="mb-4 ml-n3"
    exact
  >
    Tickets
  </v-btn>

  <v-progress-linear v-if="loading && !ticket" indeterminate color="primary" />

  <v-empty-state
    v-else-if="notFound"
    title="Ticket no disponible"
    text="El ticket no existe o no tienes acceso a él."
  >
    <template #media>
      <div class="d-flex justify-center mb-4">
        <MascotPeek cover-eyes :size="130" />
      </div>
    </template>
    <template #actions>
      <v-btn color="primary" :to="{ name: 'tickets' }">Ver mis tickets</v-btn>
    </template>
  </v-empty-state>

  <v-alert v-else-if="loadError" type="error">
    {{ loadError }}
    <template #append>
      <v-btn variant="text" @click="load">Reintentar</v-btn>
    </template>
  </v-alert>

  <template v-else-if="ticket">
    <header class="mb-6">
      <div class="text-secondary-label text-body-2 mb-1">Ticket #{{ ticket.id }}</div>
      <h2 class="text-h5 mb-3">{{ ticket.incidencia }} · {{ ticket.subincidencia }}</h2>
      <div class="d-flex flex-wrap ga-2">
        <v-chip :color="STATUS_COLORS[ticket.status]" size="default">{{ label(STATUS_LABELS, ticket.status) }}</v-chip>
        <v-chip :color="PRIORITY_COLORS[ticket.priority]" size="default" prepend-icon="flag">
          Prioridad {{ label(PRIORITY_LABELS, ticket.priority).toLowerCase() }}
        </v-chip>
      </div>
    </header>

    <v-alert v-if="ticket.status === 'cancelled'" type="error" variant="tonal" icon="ban" class="mb-4">
      <div class="font-weight-medium">Ticket cancelado</div>
      <div v-if="ticket.cancel_reason" class="text-body-2">Motivo: {{ ticket.cancel_reason }}</div>
    </v-alert>

    <!-- Solicitante: confirmar la solución y calificar -->
    <v-card v-if="isOwner && ticket.feedback_state" class="pa-5 mb-4 feedback-card">
      <div class="font-weight-medium mb-3">
        {{ ticket.feedback_state === 'confirm' ? 'Tu ticket fue resuelto' : 'Califica la atención' }}
      </div>
      <TicketFeedback :ticket="ticket" @answered="onAnswered" />
    </v-card>

    <!-- Soporte: el ticket espera respuesta del solicitante -->
    <v-alert
      v-else-if="auth.isStaff && ticket.feedback_state"
      type="info"
      variant="tonal"
      icon="clock"
      class="mb-4"
    >
      {{ ticket.feedback_state === 'confirm'
        ? 'Esperando que el solicitante confirme la solución.'
        : 'Esperando la calificación del solicitante.' }}
      Si no responde, se {{ ticket.feedback_state === 'confirm' ? 'cerrará' : 'calificará' }}
      automáticamente con 5 estrellas el {{ formatDateTime(ticket.feedback_due_at) }}.
    </v-alert>

    <v-row>
      <v-col cols="12" md="8" order="2" order-md="1">
        <TicketConversation ref="conversation" :ticket="ticket" @commented="loadHistory" />
      </v-col>

      <v-col cols="12" md="4" order="1" order-md="2" class="d-flex flex-column ga-4">
        <v-card class="pa-5">
          <dl class="details">
            <dt>Solicitante</dt>
            <dd>{{ ticket.created_by_user_name ?? '—' }}</dd>

            <dt>Ubicación</dt>
            <dd>
              <span v-if="ticket.location_name">{{ ticket.location_name }}</span>
              <span v-else class="text-secondary-label">Sin ubicación</span>
            </dd>

            <dt>Asignado a</dt>
            <dd>
              <span v-if="ticket.assigned_to_user_name">{{ ticket.assigned_to_user_name }}</span>
              <span v-else class="text-secondary-label">Sin asignar</span>
            </dd>

            <dt>Creado</dt>
            <dd :title="formatDateTime(ticket.created_at)">{{ formatDateTime(ticket.created_at) }}</dd>

            <template v-if="ticket.updated_at">
              <dt>Actualizado</dt>
              <dd :title="formatDateTime(ticket.updated_at)">{{ timeAgo(ticket.updated_at) }}</dd>
            </template>
          </dl>

          <v-btn
            v-if="canCancel && !auth.isStaff"
            block
            variant="tonal"
            color="error"
            prepend-icon="ban"
            class="mt-4"
            :loading="busy === 'cancel'"
            :disabled="!!busy"
            @click="openCancel"
          >
            Cancelar ticket
          </v-btn>
        </v-card>

        <!-- Resultado de la encuesta -->
        <v-card v-if="ticket.survey" class="pa-5">
          <div class="font-weight-medium mb-2">Calificación del servicio</div>
          <div class="d-flex align-center ga-2">
            <v-rating
              :model-value="ticket.survey.rating"
              readonly
              density="compact"
              size="22"
              color="grey-lighten-1"
              active-color="secondary"
            />
            <span class="text-body-2 font-weight-medium">{{ RATING_LABELS[ticket.survey.rating] }}</span>
          </div>
          <p v-if="ticket.survey.comment" class="text-body-2 mt-2 mb-0 survey-comment">“{{ ticket.survey.comment }}”</p>
          <p v-if="ticket.survey.is_auto" class="text-caption text-secondary-label mt-2 mb-0">
            Registrada en automático: no hubo respuesta en 24 horas.
          </p>
        </v-card>

        <!-- Acciones de soporte -->
        <v-card v-if="auth.isStaff && !closed" class="pa-5">
          <div class="font-weight-medium mb-4">Gestión</div>

          <label class="field-label">Asignado a</label>
          <div class="d-flex ga-2 mb-1">
            <v-select
              :model-value="ticket.assigned_to_user_id"
              :items="staff"
              item-title="name"
              item-value="id"
              placeholder="Elegir técnico"
              :loading="busy === 'assign'"
              :disabled="!!busy"
              hide-details
              @update:model-value="assignTo"
            />
            <v-btn
              v-if="ticket.assigned_to_user_id !== auth.user?.id"
              variant="tonal"
              color="primary"
              icon="user-plus"
              title="Asignármelo"
              :disabled="!!busy"
              @click="assignTo(auth.user.id)"
            />
          </div>
          <p class="text-caption text-secondary-label mb-4">Al asignar, el ticket pasa a En progreso.</p>

          <label class="field-label">Prioridad</label>
          <v-select
            :model-value="ticket.priority"
            :items="priorityItems"
            :loading="busy === 'priority'"
            :disabled="!!busy"
            hide-details
            class="mb-4"
            @update:model-value="changePriority"
          />

          <template v-if="nextStatuses.length">
            <label class="field-label">Cambiar estado</label>
            <div class="d-flex flex-wrap ga-2 mb-1">
              <v-btn
                v-for="s in nextStatuses"
                :key="s"
                variant="tonal"
                :color="STATUS_COLORS[s]"
                :loading="busy === 'status'"
                :disabled="!!busy || !ticket.assigned_to_user_id"
                @click="changeStatus(s)"
              >
                {{ label(STATUS_LABELS, s) }}
              </v-btn>
            </div>
            <p v-if="!ticket.assigned_to_user_id" class="text-caption text-secondary-label">
              Asigna el ticket para poder cambiar su estado.
            </p>
          </template>

          <v-divider class="my-4" />

          <v-btn
            block
            variant="tonal"
            :color="ticket.status === 'resolved' ? 'primary' : 'grey'"
            prepend-icon="lock"
            :loading="busy === 'close'"
            :disabled="!!busy"
            @click="confirmClose = true"
          >
            Cerrar ticket
          </v-btn>
          <v-btn
            v-if="canCancel"
            block
            variant="text"
            color="error"
            prepend-icon="ban"
            class="mt-2"
            :loading="busy === 'cancel'"
            :disabled="!!busy"
            @click="openCancel"
          >
            Cancelar ticket
          </v-btn>
        </v-card>

        <TicketAttachments :ticket-id="ticket.id" :closed="closed" @uploaded="loadHistory" />

        <!-- Historial (solo soporte/admin) -->
        <v-card v-if="auth.isStaff" class="pa-5">
          <div class="d-flex align-center mb-3">
            <v-icon icon="history" size="18" class="mr-2 text-secondary-label" />
            <span class="font-weight-medium">Historial</span>
          </div>
          <p v-if="!history.length" class="text-body-2 text-secondary-label">Sin movimientos registrados.</p>
          <v-timeline v-else side="end" density="compact" truncate-line="both" class="history">
            <v-timeline-item
              v-for="h in [...history].reverse()"
              :key="h.id"
              dot-color="primary"
              size="8"
            >
              <div class="text-body-2">
                <span class="font-weight-medium">{{ h.user_name ?? 'Sistema' }}</span>
                {{ historyText(h, staffById).charAt(0).toLowerCase() + historyText(h, staffById).slice(1) }}
              </div>
              <div class="text-caption text-secondary-label" :title="formatDateTime(h.created_at)">
                {{ timeAgo(h.created_at) }}
              </div>
            </v-timeline-item>
          </v-timeline>
        </v-card>
      </v-col>
    </v-row>
  </template>

  <v-dialog v-model="confirmClose" max-width="420">
    <v-card class="pa-2">
      <v-card-title class="pt-4 px-5 text-h6">¿Cerrar el ticket #{{ ticket?.id }}?</v-card-title>
      <v-card-text class="px-5">
        Un ticket cerrado ya no admite comentarios ni archivos. Se avisará al solicitante por correo
        y se le pedirá calificar la atención (si no responde en 24 h, se registra con 5 estrellas).
      </v-card-text>
      <v-card-actions class="px-5 pb-4">
        <v-spacer />
        <v-btn variant="text" @click="confirmClose = false">Cancelar</v-btn>
        <v-btn color="primary" @click="closeTicket">Cerrar ticket</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <v-dialog v-model="cancelDialog" max-width="440">
    <v-card class="pa-2">
      <v-card-title class="pt-4 px-5 text-h6">¿Cancelar el ticket #{{ ticket?.id }}?</v-card-title>
      <v-card-text class="px-5">
        <p class="text-body-2 mb-4">
          El ticket no se borra: queda como Cancelado en el historial y ya no admite cambios.
        </p>
        <label class="field-label">Motivo <span class="text-error">*</span></label>
        <v-textarea
          v-model="cancelReason"
          placeholder="Ej. se resolvió solo, se levantó por error, ticket duplicado…"
          rows="3"
          auto-grow
          :rules="[(v) => (v ?? '').trim().length >= 5 || 'Mínimo 5 caracteres']"
        />
      </v-card-text>
      <v-card-actions class="px-5 pb-4">
        <v-spacer />
        <v-btn variant="text" @click="cancelDialog = false">Volver</v-btn>
        <v-btn color="error" :disabled="cancelReason.trim().length < 5" @click="cancelTicket">Cancelar ticket</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <v-snackbar v-model="notice.show" :color="notice.color" timeout="5000" location="bottom right">
    {{ notice.text }}
  </v-snackbar>
</template>

<style scoped>
.details {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 10px 16px;
  font-size: 14px;
}
.details dt {
  color: var(--app-text-secondary);
}
.details dd {
  text-align: right;
  font-weight: 500;
}
.history {
  max-height: 360px;
  overflow-y: auto;
}
.feedback-card {
  border: 1px solid rgba(var(--v-theme-success), 0.35) !important;
}
.survey-comment {
  white-space: pre-wrap;
  font-style: italic;
}
</style>
