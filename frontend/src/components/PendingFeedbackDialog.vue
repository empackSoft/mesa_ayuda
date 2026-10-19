<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useFeedbackStore } from '../stores/feedback'
import TicketFeedback from './TicketFeedback.vue'

// Encuesta obligatoria: mientras el usuario tenga tickets por confirmar o calificar,
// esta ventana no se puede cerrar. Solo se oculta mientras ve el detalle de ese ticket
// (ahí mismo puede leer la conversación y responder).
const feedback = useFeedbackStore()
const route = useRoute()
const router = useRouter()

const current = computed(() => feedback.pending[0] ?? null)

const onItsDetail = computed(
  () => route.name === 'ticket-detail' && String(route.params.id) === String(current.value?.id),
)

const open = computed(() => Boolean(current.value) && !onItsDetail.value)

const thanks = ref('')

function onAnswered(ticket, kind) {
  thanks.value = kind === 'reopen'
    ? `Reabrimos el ticket #${ticket.id}. Soporte ya fue notificado.`
    : `¡Gracias! Registramos tu calificación del ticket #${ticket.id}.`
  feedback.remove(ticket.id)
}

function viewTicket() {
  router.push({ name: 'ticket-detail', params: { id: current.value.id } })
}

watch(() => route.fullPath, () => feedback.refresh(), { immediate: true })
</script>

<template>
  <v-dialog :model-value="open" persistent max-width="520" scrollable>
    <v-card v-if="current" class="pa-2">
      <v-card-title class="pt-4 px-5 text-h6">
        {{ current.feedback_state === 'confirm' ? 'Tu ticket fue resuelto' : 'Califica la atención' }}
      </v-card-title>
      <v-card-text class="px-5">
        <div class="ticket-summary mb-4">
          <div class="text-secondary-label text-body-2">Ticket #{{ current.id }}</div>
          <div class="font-weight-medium">{{ current.incidencia }} · {{ current.subincidencia }}</div>
          <div class="text-body-2 text-secondary-label summary-text">{{ current.description }}</div>
          <div v-if="current.assigned_to_user_name" class="text-body-2 mt-1">
            Atendido por <strong>{{ current.assigned_to_user_name }}</strong>
          </div>
          <v-btn variant="text" size="small" class="mt-1 ml-n2" @click="viewTicket">Ver conversación</v-btn>
        </div>

        <TicketFeedback :ticket="current" @answered="onAnswered" />

        <p v-if="feedback.pending.length > 1" class="text-caption text-secondary-label mt-4 mb-0">
          Tienes {{ feedback.pending.length }} tickets por responder.
        </p>
      </v-card-text>
    </v-card>
  </v-dialog>

  <v-snackbar :model-value="Boolean(thanks)" color="success" timeout="5000" location="bottom right"
    @update:model-value="thanks = ''">
    {{ thanks }}
  </v-snackbar>
</template>

<style scoped>
.ticket-summary {
  background: rgba(11, 40, 121, 0.04);
  border-radius: 12px;
  padding: 12px 14px;
}
.summary-text {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  white-space: pre-wrap;
}
</style>
