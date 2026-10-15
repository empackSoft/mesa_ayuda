<script setup>
import logoUrl from '../assets/logo-32-sin-fondo.png'

// Logo de EmPack; "size" es la altura en px (la imagen original mide 148×72)
defineProps({
  size: { type: Number, default: 36 },
  showText: { type: Boolean, default: true },
})
</script>

<template>
  <div class="brand d-flex align-center ga-3">
    <img :src="logoUrl" alt="EmPack · Cajas de cartón" :style="{ height: `${size}px` }" class="brand-logo">
    <div v-if="showText" class="brand-sub">Mesa de Ayuda</div>
  </div>
</template>

<style scoped>
.brand-logo {
  display: block;
  width: auto;
  flex-shrink: 0;
}
.brand-sub {
  font-size: 12px;
  font-weight: 500;
  color: var(--app-text-secondary);
  line-height: 1.2;
  padding-left: 12px;
  border-left: 1px solid var(--app-hairline);
}
</style>
