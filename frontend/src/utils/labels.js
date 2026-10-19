// El backend devuelve valores crudos; aquí se traducen para mostrarlos

export const ROLE_LABELS = {
  user: 'Usuario',
  support: 'Soporte',
  admin: 'Administrador',
}

export const STATUS_LABELS = {
  open: 'Abierto',
  in_progress: 'En progreso',
  pending: 'Pendiente',
  resolved: 'Resuelto',
  closed: 'Cerrado',
  cancelled: 'Cancelado',
}

export const STATUS_COLORS = {
  open: 'info',
  in_progress: 'primary',
  pending: 'warning',
  resolved: 'success',
  closed: 'grey',
  cancelled: 'error',
}

// Ya no admiten cambios, comentarios ni archivos (FINAL_STATUSES en ticketService.py)
export const FINAL_STATUSES = ['closed', 'cancelled']
export const isFinal = (status) => FINAL_STATUSES.includes(status)

// Mismo plazo que FEEDBACK_HOURS en ticketService.py
export const FEEDBACK_HOURS = 24

export const RATING_LABELS = {
  1: 'Muy mala',
  2: 'Mala',
  3: 'Regular',
  4: 'Buena',
  5: 'Excelente',
}

export const PRIORITY_LABELS = {
  low: 'Baja',
  medium: 'Media',
  high: 'Alta',
  urgent: 'Urgente',
}

export const PRIORITY_COLORS = {
  low: 'grey',
  medium: 'info',
  high: 'warning',
  urgent: 'error',
}

// Tipos de ubicación (en el mismo orden en que se muestran)
export const LOCATION_TYPE_LABELS = {
  branch: 'Sucursal',
  cedis: 'CEDIS',
  corporate: 'Corporativo',
}

export const LOCATION_TYPE_PLURALS = {
  branch: 'Sucursales',
  cedis: 'CEDIS',
  corporate: 'Corporativos',
}

export const LOCATION_TYPE_ICONS = {
  branch: 'store',
  cedis: 'warehouse',
  corporate: 'building-2',
}

export const label = (map, value) => map[value] ?? value

// Mismas transiciones que VALID_TRANSITIONS en services/ticketService.py
export const STATUS_TRANSITIONS = {
  open: ['in_progress'],
  in_progress: ['pending', 'resolved'],
  pending: ['in_progress', 'resolved'],
  resolved: ['in_progress', 'closed'],
  closed: [],
  cancelled: [],
}

// Texto de cada evento del historial (action, old_value, new_value crudos del backend)
export function historyText(item, staffById = {}) {
  const { action, old_value: oldValue, new_value: newValue } = item
  switch (action) {
    case 'CREATE':
      return 'Creó el ticket'
    case 'ASSIGN':
      return `Asignó el ticket a ${staffById[newValue] ?? `usuario #${newValue}`}`
    case 'STATUS':
    case 'UPDATE_STATUS':
      return `Cambió el estado de ${label(STATUS_LABELS, oldValue)} a ${label(STATUS_LABELS, newValue)}`
    case 'UPDATE_PRIORITY':
      return `Cambió la prioridad de ${label(PRIORITY_LABELS, oldValue)} a ${label(PRIORITY_LABELS, newValue)}`
    case 'UPDATE_DESCRIPTION':
      return 'Modificó la descripción'
    case 'UPDATE_INCIDENCIA_ID':
    case 'UPDATE_SUBINCIDENCIA_ID':
      return 'Cambió la categoría'
    case 'CLOSE':
      return 'Cerró el ticket'
    case 'CANCEL':
      return `Canceló el ticket: ${newValue}`
    case 'CONFIRM':
      return 'Confirmó la solución y cerró el ticket'
    case 'REOPEN':
      return 'Indicó que el problema continúa'
    case 'AUTO_CLOSE':
      return `Cerró el ticket automáticamente (${FEEDBACK_HOURS} h sin respuesta)`
    case 'SURVEY':
      return oldValue === 'auto'
        ? `Registró la encuesta en automático con ${newValue} estrellas`
        : `Calificó la atención con ${newValue} de 5 estrellas`
    case 'UPLOAD_ATTACHMENT':
      return 'Adjuntó un archivo'
    case 'COMMENT':
      return newValue === 'Comentario interno' ? 'Agregó una nota interna' : 'Agregó un comentario'
    default:
      return action
  }
}

// Mismas reglas que ALLOWED_EXTENSIONS / MAX_FILE_SIZE en services/ticketService.py
export const ALLOWED_EXTENSIONS = [
  '.png', '.jpg', '.jpeg', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.zip',
]
export const MAX_FILE_SIZE = 10 * 1024 * 1024
