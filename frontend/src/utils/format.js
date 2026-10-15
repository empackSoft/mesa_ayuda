// Formato de fechas y tamaños para mostrar en pantalla

// El backend guarda fechas en UTC sin zona ("2026-10-15T18:18:05"); se interpretan como UTC
export function parseDate(value) {
  if (!value) return null
  if (value instanceof Date) return value
  const hasZone = /([zZ]|[+-]\d{2}:?\d{2})$/.test(value)
  return new Date(hasZone ? value : `${value}Z`)
}

const dateTimeFmt = new Intl.DateTimeFormat('es-MX', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

const dateFmt = new Intl.DateTimeFormat('es-MX', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
})

export function formatDateTime(value) {
  const d = parseDate(value)
  return d ? dateTimeFmt.format(d) : ''
}

export function formatDate(value) {
  const d = parseDate(value)
  return d ? dateFmt.format(d) : ''
}

const relativeFmt = new Intl.RelativeTimeFormat('es-MX', { numeric: 'auto' })

// "hace 5 minutos", "ayer", etc. Después de una semana se muestra la fecha
export function timeAgo(value) {
  const d = parseDate(value)
  if (!d) return ''
  const seconds = Math.round((d.getTime() - Date.now()) / 1000)
  const abs = Math.abs(seconds)
  if (abs < 60) return 'justo ahora'
  if (abs < 3600) return relativeFmt.format(Math.round(seconds / 60), 'minute')
  if (abs < 86400) return relativeFmt.format(Math.round(seconds / 3600), 'hour')
  if (abs < 604800) return relativeFmt.format(Math.round(seconds / 86400), 'day')
  return formatDate(d)
}

export function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

// Duración legible a partir de segundos: "3 d 4 h", "5 h 20 min", "12 min"
export function formatDuration(seconds) {
  if (seconds == null) return '—'
  const s = Math.round(seconds)
  const days = Math.floor(s / 86400)
  const hours = Math.floor((s % 86400) / 3600)
  const minutes = Math.floor((s % 3600) / 60)
  if (days) return hours ? `${days} d ${hours} h` : `${days} d`
  if (hours) return minutes ? `${hours} h ${minutes} min` : `${hours} h`
  if (minutes) return `${minutes} min`
  return `${s} s`
}

export function initials(name) {
  return (name ?? '')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('')
}
