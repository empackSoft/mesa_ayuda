<script setup>
import { useRouter } from 'vue-router'
import { setUnauthorizedHandler } from './api/http'
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
</script>

<template>
  <v-app>
    <RouterView />
  </v-app>
</template>
