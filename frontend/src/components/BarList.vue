<script setup>
import { computed } from 'vue'

// Barras horizontales de una sola serie (magnitud): etiqueta, barra y valor.
// items: [{ key, label, value, text? }]  text = valor ya formateado para mostrar
const props = defineProps({
  items: { type: Array, required: true },
  emptyText: { type: String, default: 'Sin datos' },
})

const max = computed(() => Math.max(0, ...props.items.map((i) => i.value)))

function width(value) {
  if (!max.value || !value) return '0%'
  // mínimo visible para que un valor chico no desaparezca
  return `${Math.max(2, (value / max.value) * 100)}%`
}
</script>

<template>
  <div v-if="items.length" class="bar-list" role="table">
    <div v-for="item in items" :key="item.key" class="bar-row" role="row">
      <div class="bar-label text-body-2" role="cell">{{ item.label }}</div>
      <div class="bar-track" role="cell">
        <v-tooltip :text="`${item.label}: ${item.text ?? item.value}`" location="top">
          <template #activator="{ props: tip }">
            <div class="bar-hit" v-bind="tip">
              <div class="bar" :style="{ width: width(item.value) }" />
            </div>
          </template>
        </v-tooltip>
      </div>
      <div class="bar-value text-body-2" role="cell">{{ item.text ?? item.value }}</div>
    </div>
  </div>
  <p v-else class="text-body-2 text-secondary-label">{{ emptyText }}</p>
</template>

<style scoped>
.bar-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.bar-row {
  display: grid;
  grid-template-columns: minmax(90px, 140px) 1fr auto;
  align-items: center;
  gap: 12px;
}
.bar-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.bar-hit {
  padding: 6px 0;
  cursor: default;
}
.bar {
  height: 10px;
  border-radius: 0 4px 4px 0;
  background: rgb(var(--v-theme-primary));
  transition: width 0.4s ease;
}
.bar-hit:hover .bar {
  opacity: 0.8;
}
.bar-value {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  min-width: 2.5em;
  text-align: right;
}
</style>
