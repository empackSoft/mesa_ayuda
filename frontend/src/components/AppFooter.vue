<script setup>
import logoSistemasUrl from '../assets/logo-sistemas-pie.png'

// Pie de página de todo el sistema (login, vistas con menú y 404)
const year = new Date().getFullYear()
</script>

<template>
  <footer class="app-footer">
    <img :src="logoSistemasUrl" alt="EmPack Sistemas" class="app-footer-logo">
    <div>© {{ year }} EmPack · Sistemas · Creado por René M.M.</div>
  </footer>
</template>

<style scoped>
.app-footer {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 8px 16px 24px;
  font-size: 12px;
  color: var(--app-text-secondary);
  text-align: center;
}
.app-footer-logo {
  display: block;
  height: 72px;
  width: auto;
}
</style>
