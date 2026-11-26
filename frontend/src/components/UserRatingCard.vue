<script setup>
import { ref, watch } from 'vue'
import { errorMessage } from '../api/http'
import { ticketsApi } from '../api/tickets'
import { useAuthStore } from '../stores/auth'
import { formatDateTime } from '../utils/format'
import { USER_RATING_LABELS, USER_RATING_REASON_LABELS } from '../utils/labels'

// Soporte califica al usuario que levantó el ticket (la otra cara de la encuesta).
// La da el técnico asignado o un admin cuando el ticket está resuelto, cerrado o cancelado,
// y no se edita después. El usuario la ve en solo lectura, como retroalimentación.
const props = defineProps({
  ticketId: { type: [Number, String], required: true },
  status: { type: String, required: true },
})

const emit = defineEmits(['rated'])
const auth = useAuthStore()

const state = ref(null) // { rating, can_rate }
const rating = ref(0)
const reasons = ref([])
const comment = ref('')
const sending = ref(false)
const error = ref('')

const REASONS = Object.entries(USER_RATING_REASON_LABELS).map(([value, title]) => ({ value, title }))

async function load() {
  try {
    state.value = await ticketsApi.userRating(props.ticketId)
  } catch {
    state.value = null
  }
}

watch(() => [props.ticketId, props.status], load, { immediate: true })

function toggleReason(value) {
  reasons.value = reasons.value.includes(value)
    ? reasons.value.filter((r) => r !== value)
    : [...reasons.value, value]
}

async function send() {
  if (!rating.value) {
    error.value = 'Elige de 1 a 5 estrellas'
    return
  }
  sending.value = true
  error.value = ''
  try {
    state.value = await ticketsApi.rateUser(props.ticketId, {
      rating: rating.value,
      reasons: reasons.value,
      comment: comment.value.trim() || null,
    })
    emit('rated')
  } catch (e) {
    error.value = errorMessage(e, 'No se pudo guardar la calificación')
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <!-- Ya calificado -->
  <v-card v-if="state?.rating" class="pa-5">
    <div class="font-weight-medium mb-2">{{ auth.isStaff ? 'Calificación al usuario' : 'Cómo te calificó Soporte' }}</div>
    <div class="d-flex align-center ga-2">
      <v-rating
        :model-value="state.rating.rating"
        readonly
        density="compact"
        size="22"
        color="grey-lighten-1"
        active-color="secondary"
      />
      <span class="text-body-2 font-weight-medium">{{ USER_RATING_LABELS[state.rating.rating] }}</span>
    </div>
    <div v-if="state.rating.reasons.length" class="d-flex flex-wrap ga-1 mt-2">
      <v-chip v-for="r in state.rating.reasons" :key="r" size="small">{{ USER_RATING_REASON_LABELS[r] ?? r }}</v-chip>
    </div>
    <p v-if="state.rating.comment" class="text-body-2 mt-2 mb-0">“{{ state.rating.comment }}”</p>
    <p class="text-caption text-secondary-label mt-2 mb-0">
      {{ state.rating.rated_by_user_name }} · {{ formatDateTime(state.rating.created_at) }}
      <template v-if="auth.isStaff"> · el usuario también la ve</template>
    </p>
  </v-card>

  <!-- Pendiente de calificar -->
  <v-card v-else-if="state?.can_rate" class="pa-5 rate-card">
    <div class="d-flex align-center ga-2 mb-1">
      <v-icon icon="user-check" size="18" color="primary" />
      <span class="font-weight-medium">Califica al usuario</span>
    </div>
    <p class="text-caption text-secondary-label mb-3">
      ¿Respondió a tiempo y dio información correcta? El usuario verá tu calificación y comentario.
    </p>

    <v-rating v-model="rating" hover density="compact" size="28" color="grey-lighten-1" active-color="secondary" />
    <div class="text-caption text-secondary-label mb-3">{{ rating ? USER_RATING_LABELS[rating] : 'Elige de 1 a 5' }}</div>

    <div class="d-flex flex-wrap ga-1 mb-3">
      <v-chip
        v-for="r in REASONS"
        :key="r.value"
        size="small"
        :variant="reasons.includes(r.value) ? 'flat' : 'tonal'"
        :color="reasons.includes(r.value) ? 'primary' : undefined"
        @click="toggleReason(r.value)"
      >
        {{ r.title }}
      </v-chip>
    </div>

    <v-textarea
      v-model="comment"
      placeholder="Comentario (opcional)"
      rows="2"
      auto-grow
      maxlength="2000"
      hide-details
      class="mb-3"
    />

    <v-alert v-if="error" type="error" density="compact" class="mb-3">{{ error }}</v-alert>

    <v-btn color="primary" block :loading="sending" @click="send">Guardar calificación</v-btn>
  </v-card>
</template>

<style scoped>
.rate-card {
  border: 1px solid rgba(var(--v-theme-primary), 0.35);
}
</style>
