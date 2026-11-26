<script setup>
import { ref } from 'vue'
import { isTourEnabled, setTourEnabled } from '../utils/tour'

// Botón flotante de ayuda (abajo a la derecha): lanzar la visita guiada y
// activar/desactivar que aparezca al iniciar sesión.
const props = defineProps({
  userId: { type: [Number, String], default: null },
})
const emit = defineEmits(['start-tour'])

const open = ref(false)
const enabled = ref(isTourEnabled(props.userId))

function onToggle(value) {
  enabled.value = value
  setTourEnabled(props.userId, value)
}

function start() {
  open.value = false
  emit('start-tour')
}
</script>

<template>
  <v-menu v-model="open" location="top end" offset="10" :close-on-content-click="false">
    <template #activator="{ props: menuProps }">
      <v-btn
        v-bind="menuProps"
        data-tour="help"
        icon="circle-help"
        color="primary"
        size="small"
        class="help-fab"
        elevation="4"
        aria-label="Ayuda"
        title="Ayuda"
      />
    </template>

    <v-card min-width="230" class="pa-2">
      <v-list density="compact" class="pa-0">
        <v-list-item prepend-icon="map" title="Visita guiada" rounded="lg" @click="start" />
        <v-list-item rounded="lg" @click="onToggle(!enabled)">
          <template #prepend>
            <v-icon :icon="enabled ? 'eye' : 'eye-off'" />
          </template>
          <v-list-item-title>Visita {{ enabled ? 'activada' : 'desactivada' }}</v-list-item-title>
          <template #append>
            <v-switch
              :model-value="enabled"
              color="primary"
              hide-details
              inset
              density="compact"
              aria-label="Mostrar la visita al iniciar sesión"
              @click.stop
              @update:model-value="onToggle"
            />
          </template>
        </v-list-item>
      </v-list>
      <p class="text-caption text-secondary-label px-3 pb-1 mb-0">
        Activada: la visita aparece al iniciar sesión.
      </p>
    </v-card>
  </v-menu>
</template>

<style scoped>
.help-fab {
  position: fixed;
  right: 16px;
  bottom: 16px;
  z-index: 1004;
}
</style>
