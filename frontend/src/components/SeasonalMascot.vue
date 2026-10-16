<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import mascotUrl from '../assets/mascota.png'

// Mascota del menú lateral. Según la fecha (ver utils/seasons.js) lleva un accesorio
// y, cada vez que cambia "playKey" (abrir/cerrar el menú), hace una animación de temporada.
// Los accesorios y efectos son SVG en las mismas coordenadas que la imagen (224×199);
// lo que sale de ese cuadro (sombreros, papel picado) se dibuja fuera con overflow visible.
const props = defineProps({
  season: { type: String, default: null },
  size: { type: Number, default: 112 },
  playKey: { type: Number, default: 0 },
})

const MOTION = {
  'anio-nuevo': 'jump',
  reyes: 'bow',
  'amor-amistad': 'pulse',
  mujer: 'sway',
  juarez: 'nod',
  nino: 'flip',
  puebla: 'march',
  madre: 'jump',
  padre: 'nod',
  indigenas: 'sway',
  independencia: 'jump',
  tlatelolco: 'nod',
  muertos: 'sway',
  navidad: 'shiver',
}

const TRICOLOR = ['#006847', '#F1F3F5', '#CE1126']

const FX = {
  'anio-nuevo': [['confetti', ['#F7C948', '#BF0811', '#0B2879', '#1E7B45', '#BC9451']], ['sparkle', ['#F2C230']]],
  reyes: [['sparkle', ['#F2C230', '#E0A800', '#FAB005']]],
  'amor-amistad': [['hearts', ['#E64980', '#F783AC', '#D6336C']]],
  mujer: [['petals', ['#7B2CBF', '#9D4EDD', '#C77DFF']]],
  nino: [['confetti', ['#FA5252', '#FCC419', '#40C057', '#339AF0', '#CC5DE8']], ['balloons', ['#FA5252', '#339AF0', '#FCC419']]],
  puebla: [['confetti', TRICOLOR]],
  madre: [['hearts', ['#E64980', '#F783AC', '#FF8787']]],
  padre: [['sparkle', ['#0B2879', '#BC9451']]],
  indigenas: [['burst', ['#C2410C', '#FCC419', '#1C7ED6', '#2B8A3E', '#D6336C']]],
  independencia: [['confetti', TRICOLOR]],
  tlatelolco: [['dove', ['#FFFFFF']]],
  muertos: [['petals', ['#F59F00', '#E8590C', '#FD7E14', '#CC5DE8']]],
  navidad: [['snow', ['#A5C8E8', '#C5DCF0', '#8DB4DB']]],
}

const motion = computed(() => MOTION[props.season] ?? 'wiggle')
const hasFlag = computed(() => ['puebla', 'independencia'].includes(props.season))

const PAPEL_PICADO = {
  independencia: ['#006847', '#F1F3F5', '#CE1126'],
  muertos: ['#F76707', '#E64980', '#7B2CBF', '#FCC419'],
}
const papelPicado = computed(() => {
  const colors = PAPEL_PICADO[props.season]
  if (!colors) return []
  return Array.from({ length: 7 }, (_, i) => {
    const x = 4 + i * 31
    // Bandera con orilla inferior en zigzag
    let d = `M${x} -32 h26 v18`
    for (let k = 0; k < 4; k++) d += ` l-3.25 3 l-3.25 -3`
    d += ' Z'
    return { d, x, color: colors[i % colors.length] }
  })
})

const marigolds = [[60, 44], [76, 40], [93, 36], [110, 31], [126, 27]]

const playing = ref(false)
const particles = ref([])
let stopTimer = null

const rnd = (a, b) => a + Math.random() * (b - a)
const pick = (list) => list[Math.floor(Math.random() * list.length)]

function makeParticles() {
  const out = []
  for (const [kind, colors] of FX[props.season] ?? [['sparkle', ['#BC9451', '#0B2879']]]) {
    const add = (count, fn) => {
      for (let i = 0; i < count; i++) out.push({ kind, color: pick(colors), id: out.length, ...fn(i, count) })
    }
    if (kind === 'confetti') {
      add(24, () => ({
        shape: 'rect', x: rnd(-10, 234), y: rnd(-60, -30), w: rnd(4, 7), h: rnd(7, 11),
        dx: rnd(-35, 35), dy: rnd(220, 260), rot: rnd(-540, 540), s: 1, dur: rnd(1.6, 2.4), delay: rnd(0, 0.5),
      }))
    } else if (kind === 'petals') {
      add(18, () => ({
        shape: 'petal', x: rnd(-10, 234), y: rnd(-50, -20),
        dx: rnd(-40, 40), dy: rnd(220, 250), rot: rnd(-360, 360), s: rnd(0.8, 1.3), dur: rnd(2.2, 3), delay: rnd(0, 0.7),
      }))
    } else if (kind === 'snow') {
      add(28, () => ({
        shape: 'flake', x: rnd(-10, 234), y: rnd(-60, -20), r: rnd(1.6, 3.6),
        dx: rnd(-25, 25), dy: rnd(220, 250), rot: 0, s: 1, dur: rnd(2.2, 3.2), delay: rnd(0, 0.8),
      }))
    } else if (kind === 'hearts') {
      add(10, () => ({
        shape: 'heart', x: rnd(20, 204), y: rnd(120, 170),
        dx: rnd(-25, 25), dy: rnd(-190, -150), rot: rnd(-25, 25), s: rnd(0.8, 1.5), dur: rnd(1.8, 2.5), delay: rnd(0, 0.6),
      }))
    } else if (kind === 'balloons') {
      add(3, (i) => ({
        shape: 'balloon', x: 40 + i * 70 + rnd(-10, 10), y: 190,
        dx: rnd(-15, 15), dy: -260, rot: rnd(-10, 10), s: 1, dur: rnd(2.4, 2.9), delay: 0.2 + i * 0.15,
      }))
    } else if (kind === 'sparkle') {
      add(10, () => ({
        shape: 'star', x: rnd(0, 224), y: rnd(-30, 170),
        dx: 0, dy: 0, rot: 90, s: rnd(0.7, 1.4), dur: rnd(0.9, 1.3), delay: rnd(0, 1),
      }))
    } else if (kind === 'burst') {
      add(16, (i, n) => {
        const angle = (i / n) * Math.PI * 2 + rnd(-0.15, 0.15)
        const dist = rnd(95, 140)
        return {
          shape: 'diamond', x: 112, y: 85,
          dx: Math.cos(angle) * dist, dy: Math.sin(angle) * dist, rot: rnd(-180, 180), s: rnd(0.9, 1.5), dur: rnd(1.3, 1.7), delay: rnd(0, 0.25),
        }
      })
    } else if (kind === 'dove') {
      add(1, () => ({
        shape: 'dove', x: 22, y: 104, dx: 190, dy: -170, rot: -8, s: 1.2, dur: 2.6, delay: 0.1,
      }))
    }
  }
  return out
}

function particleStyle(p) {
  return {
    '--dx': `${p.dx}px`,
    '--dy': `${p.dy}px`,
    '--rot': `${p.rot}deg`,
    '--s': p.s,
    animationDuration: `${p.dur}s`,
    animationDelay: `${p.delay}s`,
  }
}

const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

function play() {
  if (reducedMotion) return
  clearTimeout(stopTimer)
  playing.value = false
  particles.value = []
  // Dos cuadros para que el navegador reinicie las animaciones CSS
  requestAnimationFrame(() =>
    requestAnimationFrame(() => {
      particles.value = makeParticles()
      playing.value = true
      const longest = Math.max(1.8, ...particles.value.map((p) => p.dur + p.delay))
      stopTimer = setTimeout(() => {
        playing.value = false
        particles.value = []
      }, longest * 1000 + 100)
    }),
  )
}

watch(() => props.playKey, play)
onMounted(play)
</script>

<template>
  <div
    class="smascot"
    :class="[`motion-${motion}`, { 'is-playing': playing }]"
    :style="{ width: `${size}px` }"
  >
    <div class="smascot-body">
      <img :src="mascotUrl" alt="Mascota de EmPack" class="smascot-layer" draggable="false">

      <svg class="smascot-layer" viewBox="0 0 224 199" aria-hidden="true">
        <g fill="none" stroke="#1d1d1f" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round">
          <!-- Papel picado (Independencia, Día de Muertos) -->
          <g v-if="papelPicado.length" class="acc acc--banner">
            <path d="M-4 -33 Q112 -27 228 -33" stroke-width="1.6" />
            <g v-for="flag in papelPicado" :key="flag.x">
              <path :d="flag.d" :fill="flag.color" stroke-width="1.4" />
              <circle :cx="flag.x + 13" cy="-24" r="3.2" fill="#fff" stroke="none" />
              <path :d="`M${flag.x + 6} -28 l2 2 l-2 2 l-2 -2 Z M${flag.x + 20} -28 l2 2 l-2 2 l-2 -2 Z`" fill="#fff" stroke="none" />
            </g>
          </g>

          <!-- Año Nuevo: gorro de fiesta -->
          <g v-if="season === 'anio-nuevo'" transform="translate(92 38) rotate(-15)">
            <g class="acc">
              <path d="M-24 0 L0 -54 L24 0 Z" fill="#F7C948" />
              <circle cx="-9" cy="-11" r="3.5" fill="#BF0811" stroke="none" />
              <circle cx="8" cy="-22" r="3.5" fill="#0B2879" stroke="none" />
              <circle cx="-3" cy="-35" r="3" fill="#1E7B45" stroke="none" />
              <path d="M-26 0 H26" stroke="#BF0811" stroke-width="5" />
              <circle cx="0" cy="-58" r="6" fill="#BF0811" />
            </g>
          </g>

          <!-- Reyes: corona -->
          <g v-if="season === 'reyes'" transform="translate(92 38) rotate(-15)">
            <g class="acc">
              <path d="M-26 0 L-29 -30 L-14 -14 L0 -36 L14 -14 L29 -30 L26 0 Z" fill="#F2C230" />
              <rect x="-27" y="-8" width="54" height="8" fill="#E0A800" />
              <circle cx="-29" cy="-32" r="3.2" fill="#F2C230" />
              <circle cx="0" cy="-38" r="3.2" fill="#F2C230" />
              <circle cx="29" cy="-32" r="3.2" fill="#F2C230" />
              <circle cx="-14" cy="-4" r="2.6" fill="#1C7ED6" stroke="none" />
              <circle cx="0" cy="-4" r="2.8" fill="#BF0811" stroke="none" />
              <circle cx="14" cy="-4" r="2.6" fill="#2B8A3E" stroke="none" />
              <circle cx="0" cy="-20" r="3.2" fill="#BF0811" stroke-width="1.6" />
            </g>
          </g>

          <!-- Amor y amistad / Día de la Madre: mejillas sonrojadas -->
          <g v-if="season === 'amor-amistad' || season === 'madre'" class="acc" stroke="none">
            <ellipse cx="80" cy="91" rx="8" ry="5" fill="#FF6B8B" opacity="0.55" />
            <ellipse cx="140" cy="80" rx="7" ry="4.5" fill="#FF6B8B" opacity="0.55" />
          </g>

          <!-- Amor y amistad: corazón en la mano -->
          <g v-if="season === 'amor-amistad'" transform="translate(190 46) rotate(12) scale(1.7)">
            <g class="acc acc--beat">
              <path d="M0 7 C-12 -1 -12 -13 -4.5 -13 C-1.5 -13 0 -10.5 0 -8.5 C0 -10.5 1.5 -13 4.5 -13 C12 -13 12 -1 0 7 Z" fill="#E64980" stroke-width="1.4" />
            </g>
          </g>

          <!-- Día de la Mujer: flor y listón morados -->
          <g v-if="season === 'mujer'">
            <g transform="translate(66 40)">
              <g class="acc">
                <circle v-for="a in [0, 72, 144, 216, 288]" :key="a" :cx="Math.cos((a * Math.PI) / 180) * 7" :cy="Math.sin((a * Math.PI) / 180) * 7" r="6" fill="#9D4EDD" stroke-width="1.6" />
                <circle r="4" fill="#FCC419" stroke-width="1.6" />
              </g>
            </g>
            <g transform="translate(142 126) rotate(-12)">
              <g class="acc">
                <path d="M0 6 C-12 -6 -6 -16 0 -10 C6 -16 12 -6 0 6 L-7 16 M0 6 L7 16" stroke="#7B2CBF" stroke-width="4.5" />
              </g>
            </g>
          </g>

          <!-- Benito Juárez: moño negro y libro de leyes -->
          <g v-if="season === 'juarez'">
            <g transform="translate(124 121) rotate(-15)">
              <g class="acc">
                <path d="M-15 -8 L-15 8 L0 0 Z M15 -8 L15 8 L0 0 Z" fill="#1d1d1f" stroke-width="1.6" />
                <rect x="-3.5" y="-3.5" width="7" height="7" rx="2" fill="#343a40" stroke-width="1.6" />
              </g>
            </g>
            <g transform="translate(22 106) rotate(-12)">
              <g class="acc">
                <rect x="-12" y="-15" width="24" height="30" rx="2" fill="#2B4D2F" />
                <path d="M-6 -7 H6 M-6 -2 H6" stroke="#F2C230" stroke-width="1.6" />
                <path d="M-12 11 H12" stroke="#F1F3F5" stroke-width="2" />
              </g>
            </g>
          </g>

          <!-- Día del Niño: gorro con hélice -->
          <g v-if="season === 'nino'" transform="translate(92 38) rotate(-15)">
            <g class="acc">
              <path d="M-25 0 A25 21 0 0 1 25 0 Z" fill="#1C7ED6" />
              <path d="M-6 -20.3 Q0 -21.2 6 -20.3 L5 0 L-5 0 Z" fill="#FCC419" stroke="none" />
              <path d="M-27 0 H27" stroke-width="3" />
              <path d="M0 -21 V-28" />
              <g transform="translate(0 -29)">
                <g class="propeller">
                  <path d="M0 0 C-6 -4 -16 -3 -17 0 C-16 3 -6 4 0 0 C6 -4 16 -3 17 0 C16 3 6 4 0 0 Z" fill="#FA5252" stroke-width="1.6" />
                </g>
              </g>
            </g>
          </g>

          <!-- Batalla de Puebla: quepí -->
          <g v-if="season === 'puebla'" transform="translate(92 38) rotate(-15)">
            <g class="acc">
              <path d="M-20 0 L-17 -30 L17 -30 L20 0 Z" fill="#1D3557" />
              <ellipse cx="0" cy="-30" rx="17" ry="4" fill="#C1121F" />
              <rect x="-20" y="-9" width="40" height="9" fill="#C1121F" />
              <path d="M-21 0 Q2 9 28 3 L22 -1 Z" fill="#111" />
              <circle cx="0" cy="-17" r="3.5" fill="#F2C230" stroke-width="1.4" />
            </g>
          </g>

          <!-- Puebla e Independencia: bandera de México en la mano -->
          <g v-if="hasFlag">
            <g class="acc">
              <path d="M187 74 L192 -4" stroke="#8B5A2B" stroke-width="3.2" />
              <circle cx="192" cy="-6" r="3" fill="#F2C230" stroke-width="1.4" />
              <g transform="translate(192 -2)">
                <g class="flag-cloth">
                  <rect x="0" y="0" width="13" height="27" fill="#006847" stroke="none" />
                  <rect x="13" y="0" width="13" height="27" fill="#FFFFFF" stroke="none" />
                  <rect x="26" y="0" width="13" height="27" fill="#CE1126" stroke="none" />
                  <circle cx="19.5" cy="13.5" r="3.4" fill="#8B5A2B" stroke="none" />
                  <rect x="0" y="0" width="39" height="27" stroke-width="1.6" />
                </g>
              </g>
            </g>
          </g>

          <!-- Día de la Madre: ramo de flores -->
          <g v-if="season === 'madre'" transform="translate(186 60)">
            <g class="acc">
              <path d="M-6 -16 L-2 -2 M0 -22 L0 -2 M7 -15 L2 -2" stroke="#2B8A3E" stroke-width="2.4" />
              <g v-for="(f, i) in [[-8, -20, '#F783AC'], [0, -27, '#FA5252'], [9, -19, '#FCC419']]" :key="i">
                <circle :cx="f[0]" :cy="f[1]" r="6.5" :fill="f[2]" stroke-width="1.6" />
                <circle :cx="f[0]" :cy="f[1]" r="2.2" fill="#fff" stroke="none" />
              </g>
              <path d="M-11 -6 L11 -6 L0 14 Z" fill="#FFDEEB" />
            </g>
          </g>

          <!-- Día del Padre: corbata y taza -->
          <g v-if="season === 'padre'">
            <g transform="translate(126 114) rotate(-15) scale(1.25)">
              <g class="acc">
                <path d="M-5 -5 H5 L3 3 H-3 Z" fill="#0B2879" stroke-width="1.6" />
                <path d="M-3 3 H3 L6 20 L0 26 L-6 20 Z" fill="#0B2879" stroke-width="1.6" />
                <path d="M-3.5 9 L4 6 M-4.5 15 L5 11.5 M-4 21 L5 17" stroke="#BC9451" stroke-width="1.6" />
              </g>
            </g>
            <g transform="translate(20 108) rotate(-8)">
              <g class="acc">
                <path d="M11 -6 C18 -6 18 6 11 6" stroke-width="2.6" />
                <rect x="-12" y="-12" width="23" height="24" rx="3" fill="#fff" />
                <text x="-0.5" y="4" text-anchor="middle" font-size="11" font-weight="700" fill="#0B2879" stroke="none" font-family="Inter Variable, sans-serif">#1</text>
              </g>
            </g>
          </g>

          <!-- Pueblos Indígenas: banda tejida con grecas -->
          <g v-if="season === 'indigenas'" transform="translate(95 37) rotate(-15)">
            <g class="acc">
              <rect x="-46" y="-6" width="92" height="12" rx="2" fill="#C2410C" />
              <path
                v-for="(c, i) in ['#FCC419', '#1C7ED6', '#2B8A3E', '#D6336C', '#FCC419', '#1C7ED6', '#2B8A3E', '#D6336C', '#FCC419']"
                :key="i"
                :d="`M${-40 + i * 10} 0 l4 -4 l4 4 l-4 4 Z`"
                :fill="c"
                stroke-width="1"
              />
            </g>
          </g>

          <!-- 2 de octubre: paloma blanca (se va volando en la animación) -->
          <g v-if="season === 'tlatelolco'" transform="translate(22 104)">
            <g class="acc acc--dove">
              <path d="M-14 2 C-8 -6 6 -8 12 -4 L18 -6 L15 0 C10 6 -2 8 -14 2 Z" fill="#fff" stroke-width="1.8" />
              <path d="M-4 -2 C-2 -14 6 -18 10 -16 C6 -10 4 -4 2 -1 Z" fill="#fff" stroke-width="1.8" />
              <circle cx="11" cy="-4" r="1.1" fill="#1d1d1f" stroke="none" />
            </g>
          </g>

          <!-- Día de Muertos: corona de cempasúchil -->
          <g v-if="season === 'muertos'" class="acc">
            <g v-for="([x, y], i) in marigolds" :key="i">
              <circle :cx="x" :cy="y" r="7.5" fill="#FFA94D" stroke="#E8590C" stroke-width="3" stroke-dasharray="2.2 1.6" />
              <circle :cx="x" :cy="y" r="2.6" fill="#D9480F" stroke="none" />
            </g>
          </g>

          <!-- Navidad: gorro de Santa -->
          <g v-if="season === 'navidad'" transform="translate(92 38) rotate(-15)">
            <g class="acc">
              <path d="M-24 0 C-20 -30 4 -50 26 -40 C31 -37 34 -31 35 -24 C24 -31 14 -28 22 0 Z" fill="#D7263D" />
              <rect x="-28" y="-9" width="56" height="13" rx="6.5" fill="#fff" />
              <circle cx="35" cy="-22" r="7" fill="#fff" />
            </g>
          </g>
        </g>
      </svg>
    </div>

    <!-- Efectos de la animación: no se mueven con la mascota -->
    <svg v-if="particles.length" class="smascot-layer smascot-fx" viewBox="0 0 224 199" aria-hidden="true">
      <g v-for="p in particles" :key="p.id" :transform="`translate(${p.x} ${p.y})`">
        <g class="fx" :class="`fx--${p.kind}`" :style="particleStyle(p)">
          <rect v-if="p.shape === 'rect'" :x="-p.w / 2" :y="-p.h / 2" :width="p.w" :height="p.h" rx="1" :fill="p.color" stroke="rgba(0,0,0,.18)" stroke-width="0.6" />
          <ellipse v-else-if="p.shape === 'petal'" rx="4.5" ry="2.6" :fill="p.color" />
          <circle v-else-if="p.shape === 'flake'" :r="p.r" :fill="p.color" />
          <path v-else-if="p.shape === 'heart'" d="M0 7 C-12 -1 -12 -13 -4.5 -13 C-1.5 -13 0 -10.5 0 -8.5 C0 -10.5 1.5 -13 4.5 -13 C12 -13 12 -1 0 7 Z" :fill="p.color" />
          <path v-else-if="p.shape === 'star'" d="M0 -8 C1 -2 2 -1 8 0 C2 1 1 2 0 8 C-1 2 -2 1 -8 0 C-2 -1 -1 -2 0 -8 Z" :fill="p.color" />
          <path v-else-if="p.shape === 'diamond'" d="M0 -6 L5 0 L0 6 L-5 0 Z" :fill="p.color" stroke="rgba(0,0,0,.25)" stroke-width="0.8" />
          <g v-else-if="p.shape === 'balloon'">
            <path d="M0 13 Q-4 22 0 30 Q4 38 0 46" fill="none" stroke="#868e96" stroke-width="1" />
            <ellipse rx="10" ry="12.5" :fill="p.color" stroke="#1d1d1f" stroke-width="1.4" />
            <path d="M-2 12 L2 12 L0 15 Z" :fill="p.color" stroke="#1d1d1f" stroke-width="1" />
            <ellipse cx="-4" cy="-5" rx="2" ry="3.5" fill="#fff" opacity="0.6" />
          </g>
          <g v-else-if="p.shape === 'dove'" fill="#fff" stroke="#1d1d1f" stroke-width="1.8" stroke-linejoin="round">
            <path d="M-14 2 C-8 -6 6 -8 12 -4 L18 -6 L15 0 C10 6 -2 8 -14 2 Z" />
            <path class="dove-wing" d="M-4 -2 C-2 -14 6 -18 10 -16 C6 -10 4 -4 2 -1 Z" />
            <circle cx="11" cy="-4" r="1.1" fill="#1d1d1f" stroke="none" />
          </g>
        </g>
      </g>
    </svg>
  </div>
</template>

<style scoped>
/* Espacio arriba para sombreros y papel picado (38 de 224 unidades) */
.smascot {
  position: relative;
  padding-top: 17%;
  user-select: none;
  transition: width 0.25s ease;
}
.smascot-body {
  position: relative;
  aspect-ratio: 224 / 199;
  transform-origin: 50% 90%;
}
.smascot-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
}
/* Mismo cuadro que la imagen (abajo del espacio para sombreros) */
.smascot-fx {
  inset: auto 0 0 0;
  height: auto;
  aspect-ratio: 224 / 199;
  pointer-events: none;
  z-index: 2;
}

.acc,
.fx,
.propeller,
.flag-cloth,
.dove-wing {
  transform-box: fill-box;
  transform-origin: 50% 100%;
}

/* ---------- Movimiento de la mascota ---------- */
.is-playing.motion-wiggle .smascot-body { animation: m-wiggle 0.9s ease-in-out; }
.is-playing.motion-jump .smascot-body { animation: m-jump 0.9s cubic-bezier(0.3, 0.7, 0.4, 1) 2; }
.is-playing.motion-pulse .smascot-body { animation: m-pulse 0.8s ease-in-out 2; }
.is-playing.motion-sway .smascot-body { animation: m-sway 2.2s ease-in-out; }
.is-playing.motion-bow .smascot-body { animation: m-bow 1.6s ease-in-out; }
.is-playing.motion-nod .smascot-body { animation: m-nod 1.8s ease-in-out; }
.is-playing.motion-flip .smascot-body { animation: m-flip 1.2s cubic-bezier(0.3, 0.7, 0.4, 1); }
.is-playing.motion-march .smascot-body { animation: m-march 1.6s ease-in-out; }
.is-playing.motion-shiver .smascot-body { animation: m-shiver 1.4s ease-in-out; }

@keyframes m-wiggle {
  0%, 100% { transform: none; }
  20% { transform: rotate(-8deg); }
  40% { transform: rotate(7deg); }
  60% { transform: rotate(-5deg); }
  80% { transform: rotate(3deg); }
}
@keyframes m-jump {
  0%, 100% { transform: none; }
  18% { transform: translateY(2%) scale(1.05, 0.94); }
  45% { transform: translateY(-15%) scale(0.97, 1.04); }
  72% { transform: translateY(0) scale(1.05, 0.95); }
  86% { transform: translateY(-3%); }
}
@keyframes m-pulse {
  0%, 100% { transform: none; }
  15% { transform: scale(1.1); }
  30% { transform: scale(1); }
  45% { transform: scale(1.12); }
  70% { transform: scale(1); }
}
@keyframes m-sway {
  0%, 100% { transform: none; }
  25% { transform: rotate(-6deg) translateX(-3%); }
  75% { transform: rotate(6deg) translateX(3%); }
}
@keyframes m-bow {
  0%, 100% { transform: none; }
  35%, 60% { transform: rotate(14deg) translateY(4%); }
}
@keyframes m-nod {
  0%, 100% { transform: none; }
  40%, 60% { transform: rotate(7deg) translateY(2%); }
}
@keyframes m-flip {
  0% { transform: none; }
  15% { transform: translateY(3%) scale(1.06, 0.92); }
  50% { transform: translateY(-22%) rotate(180deg); }
  80% { transform: translateY(0) rotate(360deg) scale(1.06, 0.94); }
  100% { transform: rotate(360deg); }
}
@keyframes m-march {
  0%, 100% { transform: none; }
  12.5%, 62.5% { transform: translateY(-5%) rotate(-4deg); }
  25%, 75% { transform: none; }
  37.5%, 87.5% { transform: translateY(-5%) rotate(4deg); }
}
@keyframes m-shiver {
  0%, 100% { transform: none; }
  5%, 15%, 25%, 35%, 45% { transform: translateX(-2.5%); }
  10%, 20%, 30%, 40%, 50% { transform: translateX(2.5%); }
  70% { transform: translateY(-10%); }
  85% { transform: translateY(0) scale(1.04, 0.96); }
}

/* ---------- Accesorios ---------- */
.is-playing .acc { animation: acc-pop 0.55s cubic-bezier(0.34, 1.56, 0.64, 1); }
.is-playing .acc--beat { animation: acc-beat 0.8s ease-in-out 2; transform-origin: 50% 50%; }
.is-playing .acc--banner { animation: acc-drop 0.7s cubic-bezier(0.34, 1.56, 0.64, 1); transform-origin: 50% 0; }
.is-playing .acc--dove { animation: none; opacity: 0; }
.is-playing .propeller { animation: propeller 0.18s linear infinite; transform-origin: 50% 50%; }
.is-playing .flag-cloth { animation: flag-wave 0.8s ease-in-out 3; transform-origin: 0 50%; }

@keyframes acc-pop {
  0% { transform: scale(0.5); opacity: 0; }
  100% { transform: none; opacity: 1; }
}
@keyframes acc-beat {
  0%, 100% { transform: none; }
  20% { transform: scale(1.25); }
  40% { transform: scale(1); }
  60% { transform: scale(1.2); }
}
@keyframes acc-drop {
  0% { transform: translateY(-30%) scaleY(0.4); opacity: 0; }
  100% { transform: none; opacity: 1; }
}
@keyframes propeller {
  0%, 100% { transform: scaleX(1); }
  50% { transform: scaleX(-1); }
}
@keyframes flag-wave {
  0%, 100% { transform: skewY(0); }
  25% { transform: skewY(-7deg) scaleX(0.95); }
  75% { transform: skewY(6deg) scaleX(0.97); }
}

/* ---------- Efectos ---------- */
.fx {
  transform-origin: 50% 50%;
  animation-name: fx-move;
  animation-timing-function: linear;
  animation-fill-mode: both;
}
.fx--hearts,
.fx--balloons,
.fx--dove { animation-timing-function: ease-in; }
.fx--burst { animation-timing-function: cubic-bezier(0.2, 0.8, 0.3, 1); }
.fx--petals { animation-name: fx-flutter; }
.fx--sparkle { animation-name: fx-twinkle; animation-timing-function: ease-in-out; }
.fx--dove .dove-wing { animation: dove-flap 0.28s ease-in-out infinite; transform-origin: 50% 100%; }

@keyframes fx-move {
  0% { transform: translate(0, 0) rotate(0) scale(var(--s)); opacity: 0; }
  10% { opacity: 1; }
  80% { opacity: 1; }
  100% { transform: translate(var(--dx), var(--dy)) rotate(var(--rot)) scale(var(--s)); opacity: 0; }
}
@keyframes fx-flutter {
  0% { transform: translate(0, 0) rotate(0) scale(var(--s)); opacity: 0; }
  10% { opacity: 1; }
  35% { transform: translate(var(--dx), calc(var(--dy) * 0.35)) rotate(calc(var(--rot) * 0.35)) scale(var(--s)); }
  70% { transform: translate(calc(var(--dx) * -0.6), calc(var(--dy) * 0.7)) rotate(calc(var(--rot) * 0.7)) scale(var(--s)); opacity: 1; }
  100% { transform: translate(calc(var(--dx) * 0.4), var(--dy)) rotate(var(--rot)) scale(var(--s)); opacity: 0; }
}
@keyframes fx-twinkle {
  0%, 100% { transform: scale(0) rotate(0); opacity: 0; }
  50% { transform: scale(var(--s)) rotate(var(--rot)); opacity: 1; }
}
@keyframes dove-flap {
  0%, 100% { transform: none; }
  50% { transform: scaleY(-0.6); }
}

@media (prefers-reduced-motion: reduce) {
  .smascot-body,
  .acc,
  .propeller,
  .flag-cloth {
    animation: none !important;
  }
}
</style>
