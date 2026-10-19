<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { errorMessage } from '../api/http'
import AppFooter from '../components/AppFooter.vue'
import BrandLogo from '../components/BrandLogo.vue'
import MascotPeek from '../components/MascotPeek.vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const form = ref(null)
const email = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref(route.query.expired ? 'Tu sesión expiró. Vuelve a iniciar sesión.' : '')

const rules = {
  required: (v) => !!v || 'Campo obligatorio',
  email: (v) => /.+@.+\..+/.test(v) || 'Correo no válido',
}

async function submit() {
  const { valid } = await form.value.validate()
  if (!valid) return

  loading.value = true
  error.value = ''
  try {
    await auth.login(email.value.trim(), password.value)
    // Solo se aceptan rutas internas para el regreso
    const redirect = typeof route.query.redirect === 'string' && route.query.redirect.startsWith('/')
      ? route.query.redirect
      : '/'
    router.replace(redirect)
  } catch (e) {
    // 429 = demasiados intentos: el backend dice cuánto esperar
    error.value = e.response?.status === 401
      ? 'Correo o contraseña incorrectos.'
      : errorMessage(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <v-main class="login-bg">
    <div class="login-wrap">
      <div class="text-center mb-2">
        <div class="d-flex justify-center mb-5">
          <BrandLogo :size="64" :show-text="false" />
        </div>
        <h1 class="login-title">Mesa de Ayuda</h1>
        <p class="text-secondary-label mt-1">Inicia sesión con tu cuenta de EmPack</p>
      </div>

      <!-- La mascota se asoma sobre la tarjeta; se tapa los ojos al mostrar la contraseña -->
      <div class="mascot-perch">
        <MascotPeek :cover-eyes="showPassword" :size="104" />
      </div>

      <v-card class="pa-6 pa-sm-8 login-card">
        <v-alert v-if="error" type="error" density="compact" class="mb-5">
          {{ error }}
        </v-alert>

        <v-form ref="form" @submit.prevent="submit">
          <label class="field-label" for="email">Correo</label>
          <v-text-field
            id="email"
            v-model="email"
            placeholder="nombre@empack.com.mx"
            type="email"
            autocomplete="username"
            :rules="[rules.required, rules.email]"
            class="mb-2"
            autofocus
          />

          <label class="field-label" for="password">Contraseña</label>
          <v-text-field
            id="password"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="current-password"
            :append-inner-icon="showPassword ? 'eye-off' : 'eye'"
            :title="showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'"
            :rules="[rules.required]"
            class="mb-1"
            @click:append-inner="showPassword = !showPassword"
          />
          <div class="text-center mb-4">
            <RouterLink :to="{ name: 'password-reset' }" class="text-body-2 forgot-link">
              ¿Olvidaste tu contraseña?
            </RouterLink>
          </div>

          <v-btn type="submit" color="primary" size="large" height="48" block :loading="loading">
            Iniciar sesión
          </v-btn>
        </v-form>
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
  font-size: 28px;
  font-weight: 600;
  letter-spacing: -0.03em;
}
.login-card {
  box-shadow: var(--app-shadow-float) !important;
  border: none !important;
}
.forgot-link {
  color: rgb(var(--v-theme-primary));
  text-decoration: none;
}
.forgot-link:hover {
  text-decoration: underline;
}
.mascot-perch {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: center;
  margin-bottom: -18px;
  pointer-events: none;
}
</style>
