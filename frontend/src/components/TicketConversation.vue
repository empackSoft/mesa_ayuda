<script setup>
import { computed, ref, watch } from 'vue'
import { errorMessage } from '../api/http'
import { ticketsApi } from '../api/tickets'
import { useAuthStore } from '../stores/auth'
import { formatDateTime, initials, timeAgo } from '../utils/format'
import { ROLE_LABELS, isFinal, label } from '../utils/labels'

const props = defineProps({
  ticket: { type: Object, required: true },
})

const emit = defineEmits(['commented'])

const auth = useAuthStore()

const comments = ref([])
const loading = ref(false)
const error = ref('')
const body = ref('')
const internal = ref(false)
const sending = ref(false)

const closed = computed(() => isFinal(props.ticket.status))

// La descripción del ticket se muestra como el primer mensaje de la conversación
const messages = computed(() => [
  {
    id: 'description',
    user_id: props.ticket.created_by_user_id,
    user_name: props.ticket.created_by_user_name,
    user_role: null,
    body: props.ticket.description,
    is_internal: false,
    created_at: props.ticket.created_at,
    isDescription: true,
  },
  ...comments.value,
])

async function load() {
  loading.value = true
  error.value = ''
  try {
    comments.value = await ticketsApi.comments(props.ticket.id)
  } catch (e) {
    error.value = errorMessage(e, 'No se pudo cargar la conversación')
  } finally {
    loading.value = false
  }
}

async function send() {
  const text = body.value.trim()
  if (!text || sending.value) return
  sending.value = true
  error.value = ''
  try {
    const comment = await ticketsApi.addComment(props.ticket.id, text, auth.isStaff && internal.value)
    comments.value.push(comment)
    body.value = ''
    internal.value = false
    emit('commented')
  } catch (e) {
    error.value = errorMessage(e, 'No se pudo enviar el comentario')
  } finally {
    sending.value = false
  }
}

function roleOf(m) {
  if (m.isDescription) return 'Solicitante'
  return m.user_role ? label(ROLE_LABELS, m.user_role) : ''
}

watch(() => props.ticket.id, load, { immediate: true })

defineExpose({ load })
</script>

<template>
  <v-card class="pa-5">
    <div class="d-flex align-center mb-4">
      <v-icon icon="message-square" size="18" class="mr-2 text-secondary-label" />
      <span class="font-weight-medium">Conversación</span>
      <v-progress-circular v-if="loading" indeterminate size="14" width="2" class="ml-3" color="primary" />
    </div>

    <v-alert v-if="error" type="error" density="compact" class="mb-4" closable @click:close="error = ''">
      {{ error }}
    </v-alert>

    <div class="thread">
      <div
        v-for="m in messages"
        :key="m.id"
        class="message"
        :class="{ 'message--internal': m.is_internal }"
      >
        <v-avatar :color="m.user_role === 'user' || m.isDescription ? 'secondary' : 'primary'" size="34" class="flex-shrink-0">
          <span class="avatar-initials">{{ initials(m.user_name) || '?' }}</span>
        </v-avatar>

        <div class="message-body">
          <div class="d-flex flex-wrap align-center ga-2 mb-1">
            <span class="font-weight-medium">{{ m.user_name ?? 'Usuario eliminado' }}</span>
            <span v-if="roleOf(m)" class="text-caption text-secondary-label">{{ roleOf(m) }}</span>
            <v-chip v-if="m.is_internal" color="warning" prepend-icon="lock" size="x-small">Nota interna</v-chip>
            <span class="text-caption text-secondary-label" :title="formatDateTime(m.created_at)">
              · {{ timeAgo(m.created_at) }}
            </span>
          </div>
          <div class="message-text">{{ m.body }}</div>
        </div>
      </div>
    </div>

    <v-divider class="my-4" />

    <div v-if="closed" class="text-body-2 text-secondary-label d-flex align-center">
      <v-icon icon="lock" size="16" class="mr-2" />
      El ticket está {{ ticket.status === 'cancelled' ? 'cancelado' : 'cerrado' }}; ya no se pueden agregar comentarios.
    </div>

    <form v-else @submit.prevent="send">
      <v-textarea
        v-model="body"
        :placeholder="internal ? 'Nota visible solo para Soporte…' : 'Escribe una respuesta…'"
        rows="3"
        auto-grow
        max-rows="12"
        hide-details
        :class="{ 'composer--internal': internal }"
        @keydown.ctrl.enter.prevent="send"
        @keydown.meta.enter.prevent="send"
      />
      <div class="d-flex flex-wrap align-center ga-3 mt-3">
        <v-switch
          v-if="auth.isStaff"
          v-model="internal"
          color="warning"
          hide-details
          inset
          density="compact"
          class="flex-grow-0"
        >
          <template #label>
            <span class="text-body-2">Nota interna <span class="text-secondary-label">(el usuario no la ve)</span></span>
          </template>
        </v-switch>
        <v-spacer />
        <span class="text-caption text-secondary-label d-none d-sm-inline">Ctrl+Enter para enviar</span>
        <v-btn
          type="submit"
          :color="internal ? 'warning' : 'primary'"
          prepend-icon="send"
          :loading="sending"
          :disabled="!body.trim()"
        >
          {{ internal ? 'Guardar nota' : 'Enviar' }}
        </v-btn>
      </div>
    </form>
  </v-card>
</template>

<style scoped>
.thread {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.message {
  display: flex;
  gap: 12px;
}
.message-body {
  flex: 1;
  min-width: 0;
}
.message-text {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.55;
}
.message--internal .message-body {
  background: rgba(178, 106, 0, 0.07);
  border: 1px solid rgba(178, 106, 0, 0.18);
  border-radius: 12px;
  padding: 10px 12px;
}
.avatar-initials {
  font-size: 12px;
  font-weight: 600;
}
.composer--internal :deep(.v-field) {
  background: rgba(178, 106, 0, 0.07) !important;
}
</style>
