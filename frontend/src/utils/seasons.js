// Fechas especiales de la mascota del menú: cada una le pone un accesorio y una animación.
// Las fechas se toman de la hora local del navegador.

export const SEASONS = {
  'anio-nuevo': { caption: () => `¡Feliz ${new Date().getFullYear()}!`, color: '#B8860B' },
  reyes: { caption: '¡Feliz Día de Reyes!', color: '#B8860B' },
  'amor-amistad': { caption: 'Mes del amor y la amistad', color: '#D6336C' },
  mujer: { caption: 'Día Internacional de la Mujer', color: '#7B2CBF' },
  juarez: { caption: 'Natalicio de Benito Juárez', color: '#1D1D1F' },
  nino: { caption: '¡Feliz Día del Niño!', color: '#1C7ED6' },
  puebla: { caption: 'Batalla de Puebla · 1862', color: '#006847' },
  madre: { caption: '¡Feliz día, mamá!', color: '#D6336C' },
  padre: { caption: '¡Feliz día, papá!', color: '#0B2879' },
  indigenas: { caption: 'Día de los Pueblos Indígenas', color: '#C2410C' },
  independencia: { caption: '¡Viva México!', color: '#006847' },
  tlatelolco: { caption: '2 de octubre no se olvida', color: '#6E6E73' },
  muertos: { caption: 'Día de Muertos', color: '#E8590C' },
  navidad: { caption: '¡Feliz Navidad!', color: '#BF0811' },
}

// El Día del Padre en México es el tercer domingo de junio; se festeja toda esa semana (lun–dom)
function isFathersDayWeek(date) {
  const firstWeekday = new Date(date.getFullYear(), 5, 1).getDay()
  const thirdSunday = 1 + ((7 - firstWeekday) % 7) + 14
  const day = date.getDate()
  return day >= thirdSunday - 6 && day <= thirdSunday
}

export function seasonFor(date = new Date()) {
  const month = date.getMonth() + 1
  const day = date.getDate()

  if (month === 1 && day === 1) return 'anio-nuevo'
  if (month === 1 && day === 6) return 'reyes'
  if (month === 2) return 'amor-amistad'
  if (month === 3 && day === 8) return 'mujer'
  if (month === 3 && day === 21) return 'juarez'
  if (month === 4 && day === 30) return 'nino'
  if (month === 5 && day === 5) return 'puebla'
  if (month === 5 && day === 10) return 'madre'
  if (month === 6 && isFathersDayWeek(date)) return 'padre'
  if (month === 8 && day === 9) return 'indigenas'
  if (month === 9) return 'independencia'
  if (month === 10 && day === 2) return 'tlatelolco'
  if (month === 11) return 'muertos'
  if (month === 12) return 'navidad'
  return null
}

// Temporada fija para todos mientras tenga valor (ej. 'muertos'); null = según la fecha
const FIXED_SEASON = 'muertos'

// Para ver una temporada sin esperar la fecha: ?mascota=navidad en cualquier URL de la app
// (?mascota=normal muestra la mascota sin accesorios)
export function currentSeason() {
  const forced = new URLSearchParams(window.location.search).get('mascota')
  if (forced === 'normal') return null
  if (forced && forced in SEASONS) return forced
  return FIXED_SEASON ?? seasonFor()
}

export function seasonCaption(season) {
  const caption = SEASONS[season]?.caption
  return typeof caption === 'function' ? caption() : caption
}
