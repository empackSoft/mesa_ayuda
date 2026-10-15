<script setup>
import { useId } from 'vue'
import mascotUrl from '../assets/mascota.png'
// Misma imagen sin las manos de los lados (se usa mientras se tapa los ojos)
import mascotNoHandsUrl from '../assets/mascota-sin-manos.png'

// Mascota de EmPack. Con "coverEyes" sube los guantes y se tapa los ojos
// (se usa en el login cuando se muestra la contraseña).
// Los guantes son un SVG encima de la imagen, en las mismas coordenadas (224×199).
defineProps({
  coverEyes: { type: Boolean, default: false },
  size: { type: Number, default: 112 },
  idle: { type: Boolean, default: true },
})

// id único por si hay más de una mascota en la página
const gloveId = `glove-${useId()}`
</script>

<template>
  <div
    class="mascot"
    :class="{ 'mascot--covered': coverEyes, 'mascot--idle': idle }"
    :style="{ width: `${size}px` }"
  >
    <img :src="mascotNoHandsUrl" alt="" class="mascot-img" draggable="false">
    <img :src="mascotUrl" alt="Mascota de EmPack" class="mascot-img mascot-img--hands" draggable="false">

    <svg class="mascot-hands" viewBox="0 0 224 199" aria-hidden="true">
      <defs>
        <!-- Guante de caricatura (dedos hacia arriba), centrado en 0,0 -->
        <g :id="gloveId" fill="#fff" stroke="#1d1d1f" stroke-width="2.4" stroke-linejoin="round">
          <ellipse cx="-19" cy="7" rx="5.5" ry="10" transform="rotate(-28 -19 7)" />
          <rect x="-18" y="-23" width="9" height="24" rx="4.5" />
          <rect x="-9" y="-26" width="9" height="27" rx="4.5" />
          <rect x="0" y="-25" width="9" height="26" rx="4.5" />
          <rect x="9" y="-20" width="8.5" height="21" rx="4.25" />
          <rect x="-19" y="-7" width="37" height="25" rx="11" />
          <rect x="-14" y="16" width="27" height="9" rx="3.5" fill="#f7941d" />
        </g>
      </defs>

      <!-- Mano izquierda sobre el ojo izquierdo -->
      <g transform="translate(89 70) rotate(-10)">
        <g class="hand hand--left">
          <use :href="`#${gloveId}`" />
        </g>
      </g>
      <!-- Mano derecha (espejo) sobre el ojo derecho -->
      <g transform="translate(120 63) rotate(12) scale(-1 1)">
        <g class="hand hand--right">
          <use :href="`#${gloveId}`" />
        </g>
      </g>
    </svg>
  </div>
</template>

<style scoped>
.mascot {
  position: relative;
  aspect-ratio: 224 / 199;
  user-select: none;
}
.mascot-img,
.mascot-hands {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}
.mascot-hands {
  overflow: visible;
  pointer-events: none;
}

/* Manos escondidas abajo; al tapar suben con un pequeño rebote */
.hand {
  transform: translateY(95px) rotate(18deg);
  opacity: 0;
  transition:
    transform 0.32s cubic-bezier(0.5, 0, 0.75, 0),
    opacity 0.2s ease 0.1s;
}
.hand--right {
  transition-delay: 0.04s, 0.14s;
}
.mascot--covered .hand {
  transform: none;
  opacity: 1;
  transition:
    transform 0.45s cubic-bezier(0.34, 1.56, 0.64, 1),
    opacity 0.12s ease;
}
.mascot--covered .hand--right {
  transition-delay: 0.06s;
}

/* Al taparse, la mascota se encoge un poquito, como apenada */
.mascot-img,
.mascot-hands {
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.mascot--covered .mascot-img,
.mascot--covered .mascot-hands {
  transform: translateY(3px) scale(0.97);
}

/* Las manos de los lados desaparecen justo cuando suben los guantes
   (debajo queda la imagen sin manos) */
.mascot-img--hands {
  transition:
    opacity 0.12s ease 0.18s,
    transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.mascot--covered .mascot-img--hands {
  opacity: 0;
  transition:
    opacity 0.1s ease,
    transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* Balanceo suave mientras espera */
.mascot--idle {
  animation: bob 2.4s ease-in-out infinite;
}
@keyframes bob {
  0%, 100% { translate: 0 0; }
  50% { translate: 0 -4px; }
}

@media (prefers-reduced-motion: reduce) {
  .mascot--idle {
    animation: none;
  }
  .hand,
  .mascot--covered .hand {
    transition: opacity 0.15s ease;
  }
}
</style>
