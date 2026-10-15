import '@fontsource-variable/inter/opsz.css'
import 'vuetify/styles'
import '../styles/app.css'

import { createVuetify } from 'vuetify'
import { es } from 'vuetify/locale'
import { icons } from './icons'

// Paleta EmPack: azul marino como principal, rojo de marca, dorado para detalles
const empack = {
  dark: false,
  colors: {
    primary: '#0B2879',
    secondary: '#BC9451',
    brand: '#BF0811',
    'brand-soft': '#D25959',
    background: '#F5F5F7',
    surface: '#FFFFFF',
    'on-background': '#1D1D1F',
    'on-surface': '#1D1D1F',
    error: '#BF0811',
    warning: '#B26A00',
    info: '#2B5797',
    success: '#1E7B45',
    grey: '#86868B',
  },
  variables: {
    'border-color': '#000000',
    'border-opacity': 0.08,
    'medium-emphasis-opacity': 0.6,
  },
}

export default createVuetify({
  locale: {
    locale: 'es',
    messages: { es },
  },
  icons,
  theme: {
    defaultTheme: 'empack',
    themes: { empack },
  },
  // Se apaga lo característico de Material (onda al clic, sombras, mayúsculas)
  defaults: {
    global: { ripple: false },
    VBtn: { variant: 'flat', rounded: 'lg', height: 40 },
    VCard: { elevation: 0, rounded: 'xl', border: true },
    VTextField: { variant: 'solo-filled', flat: true, rounded: 'lg', density: 'comfortable' },
    VSelect: { variant: 'solo-filled', flat: true, rounded: 'lg', density: 'comfortable' },
    VTextarea: { variant: 'solo-filled', flat: true, rounded: 'lg' },
    VAutocomplete: { variant: 'solo-filled', flat: true, rounded: 'lg', density: 'comfortable' },
    VChip: { variant: 'tonal', rounded: 'lg', size: 'small' },
    VAlert: { variant: 'tonal', rounded: 'lg' },
    VMenu: { offset: 6 },
    VList: { rounded: 'lg' },
    VDialog: { maxWidth: 560 },
  },
})
