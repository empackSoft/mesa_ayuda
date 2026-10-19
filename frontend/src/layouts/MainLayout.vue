<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'
import AppFooter from '../components/AppFooter.vue'
import BrandLogo from '../components/BrandLogo.vue'
import ChangePasswordDialog from '../components/ChangePasswordDialog.vue'
import NotificationBell from '../components/NotificationBell.vue'
import PendingFeedbackDialog from '../components/PendingFeedbackDialog.vue'
import SeasonalMascot from '../components/SeasonalMascot.vue'
import { useAuthStore } from '../stores/auth'
import { useFeedbackStore } from '../stores/feedback'
import { ROLE_LABELS, label } from '../utils/labels'
import { SEASONS, currentSeason, seasonCaption } from '../utils/seasons'

const auth = useAuthStore()
const feedback = useFeedbackStore()
const router = useRouter()

const showPassword = ref(false)
const passwordChanged = ref(false)
const { mobile } = useDisplay()

const drawer = ref(!mobile.value)
// En escritorio el botón de menú contrae el sidebar a solo iconos (la mascota sigue visible);
// en celular lo abre y cierra encima del contenido.
const rail = ref(false)
const isRail = computed(() => rail.value && !mobile.value)

function toggleMenu() {
  if (mobile.value) drawer.value = !drawer.value
  else rail.value = !rail.value
}

watch(mobile, (isMobile) => {
  drawer.value = !isMobile
  rail.value = false
})

// La mascota se anima cada vez que el menú se abre o se cierra
const season = currentSeason()
const caption = seasonCaption(season)
const captionColor = SEASONS[season]?.color
const mascotPlays = ref(0)
watch([drawer, isRail], () => mascotPlays.value++)

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
  feedback.clear()
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <v-navigation-drawer
    v-model="drawer"
    :temporary="mobile"
    :rail="isRail"
    rail-width="76"
    class="sidebar"
    :class="mobile ? 'sidebar--solid' : 'app-glass'"
    width="248"
  >
    <div class="sidebar-mascot" :class="{ 'sidebar-mascot--rail': isRail }">
      <SeasonalMascot :season="season" :size="isRail ? 46 : 88" :play-key="mascotPlays" />
      <div v-if="caption && !isRail" class="season-caption" :style="{ color: captionColor }">
        {{ caption }}
      </div>
    </div>

    <v-list nav density="compact" class="px-3">
      <v-list-item
        v-for="item in menu"
        :key="item.title"
        :to="item.to"
        :prepend-icon="item.icon"
        :title="isRail ? undefined : item.title"
        v-tooltip:end="{ text: item.title, disabled: !isRail }"
        :exact="item.to.name === 'home'"
        rounded="lg"
        color="primary"
        class="nav-item"
      />
    </v-list>
  </v-navigation-drawer>

  <v-app-bar flat height="60" class="app-glass topbar">
    <v-app-bar-nav-icon icon="menu" @click="toggleMenu" />
    <v-app-bar-title class="topbar-title d-none d-sm-flex">{{ $route.meta.title ?? 'Inicio' }}</v-app-bar-title>
    <v-spacer class="d-sm-none" />

    <RouterLink :to="{ name: 'home' }" class="topbar-logo" aria-label="Inicio">
      <BrandLogo :size="46" :show-text="false" />
    </RouterLink>

    <NotificationBell />

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
          <v-list-item prepend-icon="key-round" title="Cambiar contraseña" rounded="lg" @click="showPassword = true" />
          <v-list-item prepend-icon="log-out" title="Cerrar sesión" rounded="lg" @click="logout" />
        </v-list>
      </v-card>
    </v-menu>
  </v-app-bar>

  <v-main>
    <!-- El pie queda al fondo aunque la vista tenga poco contenido -->
    <div class="main-column">
      <div class="page">
        <RouterView />
      </div>
      <AppFooter />
    </div>
  </v-main>

  <ChangePasswordDialog v-model="showPassword" @changed="passwordChanged = true" />
  <PendingFeedbackDialog />

  <v-snackbar v-model="passwordChanged" color="success" timeout="4000" location="bottom right">
    Tu contraseña se actualizó.
  </v-snackbar>
</template>

<style scoped>
.sidebar {
  border-right: 1px solid var(--app-hairline) !important;
}
/* En pantallas angostas el menú se abre encima del contenido: fondo sólido para que no se transparente */
.sidebar--solid {
  background: rgb(var(--v-theme-surface)) !important;
}
.topbar {
  border-bottom: 1px solid var(--app-hairline) !important;
}
.sidebar-mascot {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14px 16px 12px;
  transition: padding 0.25s ease;
}
.sidebar-mascot--rail {
  padding: 12px 0 8px;
}
.season-caption {
  margin-top: 4px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: -0.01em;
  text-align: center;
  line-height: 1.25;
}
.topbar-logo {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  display: block;
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
.main-column {
  display: flex;
  flex-direction: column;
  min-height: calc(100dvh - 60px);
}
.page {
  flex: 1;
  width: 100%;
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
