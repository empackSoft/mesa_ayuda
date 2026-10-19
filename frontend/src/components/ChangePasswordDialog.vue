<script setup>
import { ref, watch } from 'vue'
import { errorMessage } from '../api/http'
import { accountApi } from '../api/tickets'

const open = defineModel({ type: Boolean, default: false })
const emit = defineEmits(['changed'])

const form = ref(null)
const current = ref('')
const next = ref('')
const confirm = ref('')
const show = ref(false)
const saving = ref(false)
const error = ref('')

const rules = {
  required: (v) => !!v || 'Campo obligatorio',
  length: (v) => (v ?? '').length >= 8 || 'Mínimo 8 caracteres',
  max: (v) => new TextEncoder().encode(v ?? '').length <= 72 || 'Máximo 72 caracteres',
  same: (v) => v === next.value || 'Las contraseñas no coinciden',
}

watch(open, (value) => {
  if (!value) return
  current.value = ''
  next.value = ''
  confirm.value = ''
  error.value = ''
  show.value = false
  form.value?.resetValidation()
})

async function submit() {
  const { valid } = await form.value.validate()
  if (!valid) return
  saving.value = true
  error.value = ''
  try {
    await accountApi.changePassword(current.value, next.value)
    open.value = false
    emit('changed')
  } catch (e) {
    error.value = errorMessage(e, 'No se pudo cambiar la contraseña')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <v-dialog v-model="open" max-width="440">
    <v-card class="pa-2">
      <v-card-title class="pt-4 px-5 text-h6">Cambiar contraseña</v-card-title>
      <v-card-text class="px-5">
        <v-alert v-if="error" type="error" density="compact" class="mb-4">{{ error }}</v-alert>
        <v-form ref="form" @submit.prevent="submit">
          <label class="field-label">Contraseña actual</label>
          <v-text-field
            v-model="current"
            :type="show ? 'text' : 'password'"
            autocomplete="current-password"
            :rules="[rules.required]"
            class="mb-2"
          />
          <label class="field-label">Nueva contraseña</label>
          <v-text-field
            v-model="next"
            :type="show ? 'text' : 'password'"
            autocomplete="new-password"
            :rules="[rules.required, rules.length, rules.max]"
            :append-inner-icon="show ? 'eye-off' : 'eye'"
            class="mb-2"
            @click:append-inner="show = !show"
          />
          <label class="field-label">Confirmar nueva contraseña</label>
          <v-text-field
            v-model="confirm"
            :type="show ? 'text' : 'password'"
            autocomplete="new-password"
            :rules="[rules.required, rules.same]"
          />
          <button type="submit" hidden />
        </v-form>
      </v-card-text>
      <v-card-actions class="px-5 pb-4">
        <v-spacer />
        <v-btn variant="text" :disabled="saving" @click="open = false">Cancelar</v-btn>
        <v-btn color="primary" :loading="saving" @click="submit">Guardar</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
