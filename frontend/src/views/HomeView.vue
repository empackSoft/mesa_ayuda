<script setup>
import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import { ROLE_LABELS, label } from '../utils/labels'

const auth = useAuthStore()

const firstName = computed(() => (auth.user?.name ?? '').split(' ')[0])

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return 'Buenos días'
  if (h < 19) return 'Buenas tardes'
  return 'Buenas noches'
})

const shortcuts = computed(() => [
  {
    title: auth.isStaff ? 'Tickets' : 'Mis tickets',
    text: auth.isStaff ? 'Atender y dar seguimiento a las solicitudes' : 'Crear y consultar tus solicitudes',
    icon: 'ticket',
    to: { name: 'tickets' },
    show: true,
  },
  {
    title: 'Dashboard',
    text: 'Indicadores y tiempos de resolución',
    icon: 'chart-column',
    to: { name: 'dashboard' },
    show: auth.isStaff,
  },
  {
    title: 'Usuarios',
    text: 'Altas, roles y accesos',
    icon: 'users',
    to: { name: 'users' },
    show: auth.isAdmin,
  },
].filter((s) => s.show))
</script>

<template>
  <header class="mb-8">
    <p class="text-secondary-label mb-1">{{ greeting }}</p>
    <h2 class="text-h4">{{ firstName }}</h2>
    <v-chip color="primary" class="mt-3">{{ label(ROLE_LABELS, auth.role) }}</v-chip>
  </header>

  <v-row>
    <v-col v-for="s in shortcuts" :key="s.title" cols="12" sm="6" lg="4">
      <v-card :to="s.to" class="pa-5 h-100">
        <div class="icon-tile mb-4">
          <v-icon :icon="s.icon" size="22" />
        </div>
        <div class="text-subtitle-1 font-weight-semibold">{{ s.title }}</div>
        <div class="text-body-2 text-secondary-label mt-1">{{ s.text }}</div>
      </v-card>
    </v-col>
  </v-row>
</template>

<style scoped>
.icon-tile {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: rgba(11, 40, 121, 0.08);
  color: rgb(var(--v-theme-primary));
}
.font-weight-semibold {
  font-weight: 600;
}
</style>
