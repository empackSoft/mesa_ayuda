<script setup>
import { useRouter } from 'vue-router'
import { setUnauthorizedHandler, TOKEN_KEY } from './api/http'
import { useAuthStore } from './stores/auth'

const router = useRouter()
const auth = useAuthStore()

// Token vencido durante el uso: cerrar sesión y volver al login
setUnauthorizedHandler(() => {
  auth.logout()
  const current = router.currentRoute.value
  if (current.name !== 'login') {
    router.push({ name: 'login', query: { redirect: current.fullPath, expired: '1' } })
  }
})

// Las pestañas comparten la sesión (localStorage): si en otra se entra con otra cuenta
// o se cierra sesión, esta se recarga para no seguir mostrando (ni avisando) al usuario anterior
window.addEventListener('storage', (event) => {
  if (event.key === TOKEN_KEY && event.newValue !== auth.token) {
    window.location.reload()
  }
})
</script>

<template>
  <v-app>
    <RouterView />
  </v-app>
</template>
