<script setup>
import MascotPeek from '../components/MascotPeek.vue'
</script>

<template>
  <v-main>
    <v-empty-state
      title="Página no encontrada"
      text="La dirección que abriste no existe."
    >
      <template #media>
        <div class="d-flex justify-center mb-4">
          <MascotPeek :size="150" />
        </div>
      </template>
      <template #actions>
        <v-btn color="primary" :to="{ name: 'home' }">Ir al inicio</v-btn>
      </template>
    </v-empty-state>
  </v-main>
</template>
