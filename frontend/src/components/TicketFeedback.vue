<script setup>
import { computed, ref, watch } from 'vue'
import { errorMessage } from '../api/http'
import { ticketsApi } from '../api/tickets'
import { formatDateTime } from '../utils/format'
import { RATING_LABELS } from '../utils/labels'

// Respuesta del solicitante a un ticket resuelto/cerrado:
// - "confirm": ¿se solucionó? Sí → califica (obligatorio) y se cierra. No → explica y se reabre.
// - "survey": ya está cerrado; solo falta calificar.
const props = defineProps({
  ticket: { type: Object, required: true },
})

const emit = defineEmits(['answered'])

const choice = ref(null) // 'yes' | 'no'
const rating = ref(0)
const comment = ref('')
const reason = ref('')
const sending = ref(false)
const error = ref('')

const state = computed(() => props.ticket.feedback_state)
const askRating = computed(() => state.value === 'survey' || choice.value === 'yes')

watch(
  () => props.ticket.id,
  () => {
    choice.value = null
    rating.value = 0
    comment.value = ''
    reason.value = ''
    error.value = ''
  },
)

async function sendSurvey() {
  if (!rating.value) {
    error.value = 'Elige de 1 a 5 estrellas'
    return
  }
  await send(() => ticketsApi.survey(props.ticket.id, rating.value, comment.value.trim() || null), 'survey')
}

async function sendReopen() {
  if (reason.value.trim().length < 5) {
    error.value = 'Cuéntanos qué sigue fallando (mínimo 5 caracteres)'
    return
  }
  await send(() => ticketsApi.reopen(props.ticket.id, reason.value.trim()), 'reopen')
}

async function send(action, kind) {
  sending.value = true
  error.value = ''
  try {
    const ticket = await action()
    emit('answered', ticket, kind)
  } catch (e) {
    error.value = errorMessage(e, 'No se pudo enviar tu respuesta')
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div>
    <template v-if="state === 'confirm'">
      <p class="mb-1 font-weight-medium">¿Se solucionó tu problema?</p>
      <p class="text-body-2 text-secondary-label mb-4">
        Soporte marcó este ticket como resuelto. Si no respondes antes del
        <strong>{{ formatDateTime(ticket.feedback_due_at) }}</strong>, se cerrará automáticamente con 5 estrellas.
      </p>
      <div class="d-flex flex-wrap ga-2 mb-2">
        <v-btn
          :variant="choice === 'yes' ? 'flat' : 'tonal'"
          color="success"
          prepend-icon="thumbs-up"
          :disabled="sending"
          @click="choice = 'yes'; error = ''"
        >
          Sí, quedó resuelto
        </v-btn>
        <v-btn
          :variant="choice === 'no' ? 'flat' : 'tonal'"
          color="warning"
          prepend-icon="thumbs-down"
          :disabled="sending"
          @click="choice = 'no'; error = ''"
        >
          No, sigue el problema
        </v-btn>
      </div>
    </template>

    <p v-else class="text-body-2 text-secondary-label mb-2">
      Califica la atención que recibiste. Si no respondes antes del
      <strong>{{ formatDateTime(ticket.feedback_due_at) }}</strong>, se registrará con 5 estrellas.
    </p>

    <div v-if="askRating" class="mt-3">
      <label class="field-label">¿Cómo calificas la atención? <span class="text-error">*</span></label>
      <div class="d-flex align-center flex-wrap ga-2 mb-2">
        <v-rating
          v-model="rating"
          length="5"
          color="grey-lighten-1"
          active-color="secondary"
          hover
          size="36"
          :disabled="sending"
        />
        <span v-if="rating" class="text-body-2 font-weight-medium">{{ RATING_LABELS[rating] }}</span>
      </div>
      <v-textarea
        v-model="comment"
        placeholder="Comentario (opcional)"
        maxlength="2000"
        rows="2"
        auto-grow
        max-rows="6"
        hide-details
        class="mb-3"
        :disabled="sending"
      />
      <v-btn color="primary" block :loading="sending" @click="sendSurvey">
        {{ state === 'confirm' ? 'Cerrar ticket y enviar calificación' : 'Enviar calificación' }}
      </v-btn>
    </div>

    <div v-if="choice === 'no'" class="mt-3">
      <label class="field-label">¿Qué sigue fallando? <span class="text-error">*</span></label>
      <v-textarea
        v-model="reason"
        placeholder="Describe qué no quedó resuelto"
        maxlength="2000"
        rows="3"
        auto-grow
        hide-details
        class="mb-3"
        :disabled="sending"
      />
      <v-btn color="warning" block prepend-icon="rotate-ccw" :loading="sending" @click="sendReopen">
        Reabrir ticket
      </v-btn>
    </div>

    <v-alert v-if="error" type="error" density="compact" class="mt-3">{{ error }}</v-alert>
  </div>
</template>
