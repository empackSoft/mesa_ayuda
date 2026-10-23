<script setup>
import { timeAgo } from '../utils/format'

// Tarjetas tipo iOS en la esquina inferior derecha. Cada una se desvanece sola
// a los 30 s (el tiempo se pausa con el mouse encima); al tocarla se abre la campanita.
defineProps({
  toasts: { type: Array, required: true },
  // Pide activar sonido y notificaciones del navegador
  askActivation: { type: Boolean, default: false },
})

const emit = defineEmits(['open', 'dismiss', 'pause', 'resume', 'activate', 'skip-activation'])

const ICONS = {
  new_ticket: 'ticket',
  ticket_update: 'bell',
}
</script>

<template>
  <Teleport to="body">
    <div class="toast-stack" aria-live="polite">
      <TransitionGroup name="toast">
        <div v-if="askActivation" key="activation" class="toast toast--activation" role="alert">
          <div class="toast-icon"><v-icon icon="volume-2" size="18" /></div>
          <div class="toast-content">
            <div class="toast-title">Activa sonido y notificaciones</div>
            <div class="toast-body">
              Así te enterarás de los avisos nuevos aunque estés en otra pestaña.
            </div>
            <div class="d-flex ga-2 mt-2">
              <v-btn size="small" color="primary" @click="emit('activate')">Activar</v-btn>
              <v-btn size="small" variant="text" @click="emit('skip-activation')">Ahora no</v-btn>
            </div>
          </div>
        </div>

        <div
          v-for="t in toasts"
          :key="t.id"
          class="toast"
          role="button"
          tabindex="0"
          @click="emit('open', t)"
          @keydown.enter="emit('open', t)"
          @mouseenter="emit('pause', t)"
          @mouseleave="emit('resume', t)"
        >
          <div class="toast-icon" :class="{ 'toast-icon--ticket': t.kind === 'new_ticket' }">
            <v-icon :icon="ICONS[t.kind] ?? 'bell'" size="18" />
          </div>
          <div class="toast-content">
            <div class="d-flex align-center">
              <span class="toast-app">Mesa de Ayuda</span>
              <v-spacer />
              <span class="toast-time">{{ timeAgo(t.created_at) }}</span>
            </div>
            <div class="toast-title">{{ t.title }}</div>
            <div v-if="t.body" class="toast-body">{{ t.body }}</div>
          </div>
          <button class="toast-close" title="Descartar" @click.stop="emit('dismiss', t)">
            <v-icon icon="x" size="14" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-stack {
  position: fixed;
  right: 16px;
  bottom: 16px;
  z-index: 3000;
  display: flex;
  flex-direction: column-reverse;
  gap: 10px;
  width: min(340px, calc(100vw - 32px));
  pointer-events: none;
}
.toast {
  position: relative;
  display: flex;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 18px;
  background: rgb(var(--v-theme-surface));
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.14), 0 2px 6px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  pointer-events: auto;
  text-align: left;
}
.toast--activation {
  cursor: default;
}
.toast:hover .toast-close,
.toast:focus-visible .toast-close {
  opacity: 1;
}
.toast-icon {
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  color: #fff;
  background: rgb(var(--v-theme-primary));
}
.toast-icon--ticket {
  background: rgb(var(--v-theme-secondary));
}
.toast-content {
  flex: 1;
  min-width: 0;
}
.toast-app {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--app-text-secondary);
}
.toast-time {
  font-size: 11px;
  color: var(--app-text-secondary);
}
.toast-title {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.3;
  margin-top: 1px;
}
.toast-body {
  font-size: 13px;
  line-height: 1.35;
  color: var(--app-text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.toast-close {
  position: absolute;
  top: -6px;
  left: -6px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
  opacity: 0;
  transition: opacity 0.15s ease;
}
@media (hover: none) {
  .toast-close {
    opacity: 1;
  }
}

/* Entra deslizándose desde abajo; sale desvaneciéndose */
.toast-enter-active {
  transition: transform 0.35s cubic-bezier(0.2, 0.9, 0.3, 1.2), opacity 0.25s ease;
}
.toast-leave-active {
  transition: opacity 0.6s ease, transform 0.6s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateY(24px) scale(0.96);
}
.toast-leave-to {
  opacity: 0;
  transform: scale(0.96);
}
.toast-move {
  transition: transform 0.3s ease;
}
</style>
