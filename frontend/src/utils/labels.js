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
}

export const STATUS_COLORS = {
  open: 'info',
  in_progress: 'primary',
  pending: 'warning',
  resolved: 'success',
  closed: 'grey',
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
  resolved: ['closed'],
  closed: [],
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
