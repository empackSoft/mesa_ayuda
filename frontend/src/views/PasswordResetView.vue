<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { errorMessage } from '../api/http'
import { accountApi } from '../api/tickets'
import AppFooter from '../components/AppFooter.vue'
import BrandLogo from '../components/BrandLogo.vue'

// Sin token: pide el correo y manda el link. Con ?token=… (link del correo): pide la nueva contraseña.
const route = useRoute()
const token = computed(() => (typeof route.query.token === 'string' ? route.query.token : ''))

const form = ref(null)
const email = ref('')
const password = ref('')
const confirm = ref('')
const show = ref(false)
const loading = ref(false)
const error = ref('')
const done = ref('')

const rules = {
  required: (v) => !!v || 'Campo obligatorio',
  email: (v) => /.+@.+\..+/.test(v) || 'Correo no válido',
  length: (v) => (v ?? '').length >= 8 || 'Mínimo 8 caracteres',
  max: (v) => new TextEncoder().encode(v ?? '').length <= 72 || 'Máximo 72 caracteres',
  same: (v) => v === password.value || 'Las contraseñas no coinciden',
}

async function submit() {
  const { valid } = await form.value.validate()
  if (!valid) return
  loading.value = true
  error.value = ''
  try {
    const result = token.value
      ? await accountApi.resetPassword(token.value, password.value)
      : await accountApi.forgotPassword(email.value.trim())
    done.value = result.message
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <v-main class="login-bg">
    <div class="login-wrap">
      <div class="text-center mb-6">
        <div class="d-flex justify-center mb-5">
          <BrandLogo :size="64" :show-text="false" />
        </div>
        <h1 class="login-title">{{ token ? 'Nueva contraseña' : '¿Olvidaste tu contraseña?' }}</h1>
        <p class="text-secondary-label mt-1">
          {{ token
            ? 'Elige una contraseña nueva para tu cuenta.'
            : 'Escribe tu correo y te enviaremos un link para restablecerla.' }}
        </p>
      </div>

      <v-card class="pa-6 pa-sm-8 login-card">
        <template v-if="done">
          <v-alert type="success" variant="tonal" class="mb-5">{{ done }}</v-alert>
          <p v-if="!token" class="text-body-2 text-secondary-label mb-5">
            El link vence en 1 hora. Si no llega, revisa tu carpeta de correo no deseado.
          </p>
          <v-btn color="primary" size="large" height="48" block :to="{ name: 'login' }">Ir a iniciar sesión</v-btn>
        </template>

        <template v-else>
          <v-alert v-if="error" type="error" density="compact" class="mb-5">{{ error }}</v-alert>

          <v-form ref="form" @submit.prevent="submit">
            <template v-if="!token">
              <label class="field-label" for="email">Correo</label>
              <v-text-field
                id="email"
                v-model="email"
                placeholder="nombre@empack.com.mx"
                type="email"
                autocomplete="username"
                :rules="[rules.required, rules.email]"
                class="mb-4"
                autofocus
              />
            </template>

            <template v-else>
              <label class="field-label" for="password">Nueva contraseña</label>
              <v-text-field
                id="password"
                v-model="password"
                :type="show ? 'text' : 'password'"
                autocomplete="new-password"
                :append-inner-icon="show ? 'eye-off' : 'eye'"
                :rules="[rules.required, rules.length, rules.max]"
                class="mb-2"
                autofocus
                @click:append-inner="show = !show"
              />
              <label class="field-label" for="confirm">Confirmar contraseña</label>
              <v-text-field
                id="confirm"
                v-model="confirm"
                :type="show ? 'text' : 'password'"
                autocomplete="new-password"
                :rules="[rules.required, rules.same]"
                class="mb-4"
              />
            </template>

            <v-btn type="submit" color="primary" size="large" height="48" block :loading="loading">
              {{ token ? 'Guardar contraseña' : 'Enviar link' }}
            </v-btn>
          </v-form>

          <div class="text-center mt-4">
            <RouterLink :to="{ name: 'login' }" class="text-body-2 link">Volver a iniciar sesión</RouterLink>
          </div>
        </template>
      </v-card>

      <AppFooter class="mt-8" />
    </div>
  </v-main>
</template>

<style scoped>
.login-bg {
  min-height: 100vh;
  background:
    radial-gradient(1200px 600px at 50% -10%, rgba(11, 40, 121, 0.08), transparent 60%),
    #f5f5f7;
}
.login-wrap {
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
  padding: 8vh 16px 32px;
}
.login-title {
  font-size: 26px;
  font-weight: 600;
  letter-spacing: -0.03em;
}
.login-card {
  box-shadow: var(--app-shadow-float) !important;
  border: none !important;
}
.link {
  color: rgb(var(--v-theme-primary));
  text-decoration: none;
}
.link:hover {
  text-decoration: underline;
}
</style>
