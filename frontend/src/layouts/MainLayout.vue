<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'
import BrandLogo from '../components/BrandLogo.vue'
import { useAuthStore } from '../stores/auth'
import { ROLE_LABELS, label } from '../utils/labels'

const auth = useAuthStore()
const router = useRouter()
const { mobile } = useDisplay()

const drawer = ref(!mobile.value)

const MENU = [
  { title: 'Inicio', icon: 'house', to: { name: 'home' } },
  { title: 'Tickets', icon: 'ticket', to: { name: 'tickets' } },
  { title: 'Dashboard', icon: 'chart-column', to: { name: 'dashboard' }, roles: ['support', 'admin'] },
  { title: 'Catálogos', icon: 'shapes', to: { name: 'catalogs' }, roles: ['admin'] },
  { title: 'Usuarios', icon: 'users', to: { name: 'users' }, roles: ['admin'] },
]

const menu = computed(() => MENU.filter((item) => !item.roles || item.roles.includes(auth.role)))

const initials = computed(() =>
  (auth.user?.name ?? '')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join(''),
)

function logout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <v-navigation-drawer v-model="drawer" :temporary="mobile" class="app-glass sidebar" width="248">
    <div class="px-5 pt-6 pb-5">
      <BrandLogo />
    </div>

    <v-list nav density="compact" class="px-3">
      <v-list-item
        v-for="item in menu"
        :key="item.title"
        :to="item.to"
        :prepend-icon="item.icon"
        :title="item.title"
        :exact="item.to.name === 'home'"
        rounded="lg"
        color="primary"
        class="nav-item"
      />
    </v-list>
  </v-navigation-drawer>

  <v-app-bar flat height="60" class="app-glass topbar">
    <v-app-bar-nav-icon icon="menu" @click="drawer = !drawer" />
    <v-app-bar-title class="topbar-title">{{ $route.meta.title ?? 'Inicio' }}</v-app-bar-title>

    <v-menu location="bottom end">
      <template #activator="{ props }">
        <v-btn v-bind="props" variant="text" class="mr-3 px-2" height="44">
          <v-avatar color="primary" size="32" class="mr-2">
            <span class="avatar-initials">{{ initials }}</span>
          </v-avatar>
          <span class="d-none d-sm-inline">{{ auth.user?.name }}</span>
          <v-icon icon="chevron-down" size="16" end class="text-secondary-label" />
        </v-btn>
      </template>

      <v-card min-width="240" class="pa-2">
        <div class="px-3 pt-2 pb-3">
          <div class="font-weight-medium">{{ auth.user?.name }}</div>
          <div class="text-body-2 text-secondary-label">{{ auth.user?.email }}</div>
          <v-chip color="primary" class="mt-2">{{ label(ROLE_LABELS, auth.role) }}</v-chip>
        </div>
        <v-divider class="mb-1" />
        <v-list density="compact" class="pa-0">
          <v-list-item prepend-icon="log-out" title="Cerrar sesión" rounded="lg" @click="logout" />
        </v-list>
      </v-card>
    </v-menu>
  </v-app-bar>

  <v-main>
    <div class="page">
      <RouterView />
    </div>
  </v-main>
</template>

<style scoped>
.sidebar {
  border-right: 1px solid var(--app-hairline) !important;
}
.topbar {
  border-bottom: 1px solid var(--app-hairline) !important;
}
.topbar-title {
  font-weight: 600;
  font-size: 17px;
  letter-spacing: -0.02em;
}
.nav-item {
  min-height: 38px !important;
  margin-bottom: 2px;
  font-weight: 500;
}
.nav-item :deep(.v-list-item__prepend > .v-icon) {
  opacity: 0.85;
  font-size: 19px;
}
.avatar-initials {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0;
}
.page {
  max-width: 1280px;
  margin: 0 auto;
  padding: 32px 24px 48px;
}
@media (max-width: 600px) {
  .page {
    padding: 20px 16px 32px;
  }
}
</style>
