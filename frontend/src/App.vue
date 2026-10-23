<script setup>
import { useRouter } from 'vue-router'
import { setUnauthorizedHandler } from './api/http'
import { USER_KEY, useAuthStore } from './stores/auth'

const router = useRouter()
const auth = useAuthStore()

// Sesión vencida durante el uso (o contraseña cambiada en otro lado): volver al login
setUnauthorizedHandler(() => {
  auth.clear()
  const current = router.currentRoute.value
  if (current.name !== 'login') {
    router.push({ name: 'login', query: { redirect: current.fullPath, expired: '1' } })
  }
})

// Las pestañas comparten la sesión (la cookie): si en otra se entra con otra cuenta
// o se cierra sesión, esta se recarga para no seguir mostrando (ni avisando) al usuario anterior
window.addEventListener('storage', (event) => {
  if (event.key !== USER_KEY) return
  let other = null
  try {
    other = JSON.parse(event.newValue)
  } catch {
    other = null
  }
  if (other?.id !== auth.user?.id) window.location.reload()
})
</script>

<template>
  <v-app>
    <RouterView />
  </v-app>
</template>
