import { driver } from 'driver.js'
import 'driver.js/dist/driver.css'

// Visita guiada (sin IA): resalta las opciones reales de la pantalla y explica cada paso,
// con el contenido del Manual de usuario. Cada vista tiene su propia visita: se muestra
// la de la pantalla donde está el usuario. Los elementos se marcan con data-tour="..."
// o se ubican por el título de su tarjeta.
// Aparece al iniciar sesión mientras el usuario no la desactive en el botón de ayuda.

const PREF_KEY = 'mesa_tour_enabled'
const PENDING_KEY = 'mesa_login_pending'

function prefKey(userId) {
  return `${PREF_KEY}_${userId ?? 'anon'}`
}

export function isTourEnabled(userId) {
  try {
    return localStorage.getItem(prefKey(userId)) !== '0'
  } catch {
    return true
  }
}

export function setTourEnabled(userId, enabled) {
  try {
    localStorage.setItem(prefKey(userId), enabled ? '1' : '0')
  } catch {
    // sin almacenamiento: solo dura esta sesión
  }
}

// El login deja una marca; el layout la toma una sola vez (visita y sonido de bienvenida)
// y la quita, así no se repiten al recargar la página.
export function markLoginPending() {
  try {
    sessionStorage.setItem(PENDING_KEY, '1')
  } catch {
    // ignorar
  }
}

export function takeLoginPending() {
  try {
    const pending = sessionStorage.getItem(PENDING_KEY) === '1'
    sessionStorage.removeItem(PENDING_KEY)
    return pending
  } catch {
    return false
  }
}

// --- Cómo encontrar los elementos ---
const $ = (name) => () => document.querySelector(`[data-tour="${name}"]`)

// Tarjeta cuyo título empieza con el texto dado (p. ej. "Tickets por estado")
const card = (title) => () => {
  const titles = document.querySelectorAll('.section-title, .font-weight-medium')
  for (const el of titles) {
    if (el.textContent.trim().startsWith(title)) return el.closest('.v-card')
  }
  return null
}

function isVisible(el) {
  if (!el) return false
  const r = el.getBoundingClientRect()
  return r.width > 0 && r.height > 0
}

const step = (element, title, description, side, align) => ({
  element,
  popover: { title, description, side, align },
})

// --- Pasos comunes ---
const HELP = step($('help'), '¿Dudas?', 'En cada pantalla puedes abrir aquí su visita guiada, o desactivar que salga al iniciar sesión.', 'left', 'end')

// --- Visitas por vista ---
const TOURS = {
  home: ({ isStaff }) => [
    {
      popover: {
        title: '¡Bienvenido a la Mesa de Ayuda!',
        description: 'Te muestro lo principal. En cada pantalla puedes abrir su propia visita desde el botón de ayuda. Sal cuando quieras con la X o la tecla Esc.',
      },
    },
    step($('menu'), 'Menú', `Desde aquí te mueves por el sistema: Inicio, Tickets${isStaff ? ', Dashboard' : ''} y más.`, 'right'),
    step($('home-shortcuts'), 'Accesos rápidos', 'Entra directo a tus tickets o a las secciones que más usas.', 'bottom'),
    step($('bell'), 'Avisos', 'La campanita te avisa cuando te asignan técnico, te responden o se resuelve un ticket. Al abrir un aviso vas directo al ticket.', 'bottom', 'end'),
    step($('account'), 'Tu cuenta', 'Aquí cambias tu contraseña y cierras sesión.', 'bottom', 'end'),
    HELP,
  ],

  tickets: ({ isStaff }) => [
    step($('new-ticket'), 'Levanta un ticket', 'Da clic en <b>Nuevo ticket</b>, elige la categoría y subcategoría, describe qué pasa y, si quieres, adjunta fotos o archivos (puedes pegar una captura con Ctrl+V).', 'bottom', 'end'),
    step($('status-tabs'), 'Filtra por estado', 'Activos, Todos, o un estado en particular. El número indica cuántos tickets hay en cada uno.', 'bottom'),
    step($('ticket-search'), 'Busca', 'Por número (por ejemplo #3586), sucursal, descripción, categoría o persona.', 'bottom'),
    step($('priority-filter'), 'Prioridad', 'Muestra solo los tickets de una prioridad.', 'bottom'),
    isStaff && step(() => document.querySelector('[data-tour="priority-filter"]')?.parentElement?.querySelector('.v-switch'), 'Asignados a mí', 'Actívalo para ver solo los tickets que tienes asignados.', 'bottom'),
    isStaff && step($('staff-filters'), 'Solicitante, sucursal y fechas', 'Combínalos: por ejemplo, los tickets de una sucursal en un año, o los de una persona en un rango de fechas. Revisa la pestaña <b>Todos</b> para incluir los cerrados.', 'bottom'),
    step($('tickets-table'), 'Lista de tickets', 'Da clic en un ticket para ver la conversación, los archivos y su estado. Las columnas se pueden ordenar.', 'top'),
    HELP,
  ],

  'ticket-detail': ({ isStaff }) => [
    step($('ticket-feedback'), 'Confirma y califica', 'Soporte marcó tu ticket como resuelto: confirma si quedó solucionado y califica la atención, o reábrelo si el problema sigue.', 'bottom'),
    step(() => document.querySelector('[data-tour="ticket-conversation"] .v-card'), 'Conversación', isStaff
      ? 'Responde al usuario o escribe una <b>nota interna</b> (solo la ve Soporte). Ctrl+Enter envía.'
      : 'Aquí platicas con Soporte. Escribe abajo y da clic en Enviar (o Ctrl+Enter).', 'right'),
    step($('ticket-details'), 'Datos del ticket', 'Quién lo levantó, quién lo atiende, la ubicación y las fechas.', 'left'),
    step($('ticket-cancel'), 'Cancelar', 'Si ya no necesitas la ayuda (se resolvió solo, fue por error o está duplicado), cancélalo con un motivo. No se borra: queda como Cancelado.', 'left'),
    isStaff && step(card('Gestión'), 'Gestión', 'Asigna el ticket, cambia prioridad y estado, márcalo como resuelto o ciérralo.', 'left'),
    step($('ticket-user-rating'), 'Calificación al usuario', isStaff
      ? 'Al terminar el ticket, califica si el usuario respondió y dio información correcta. El usuario también la ve.'
      : 'Cómo te calificó Soporte: si respondiste a tiempo y diste información correcta.', 'left'),
    step($('ticket-attachments'), 'Adjuntos', 'Fotos, PDF, Word, Excel o ZIP de hasta 10 MB. Puedes arrastrarlos o pegar una captura con Ctrl+V.', 'left'),
    isStaff && step(card('Historial'), 'Historial', 'Todo lo que le ha pasado al ticket: asignaciones, cambios de estado y calificaciones.', 'left'),
    HELP,
  ],

  dashboard: () => [
    step($('dash-kpis'), 'Indicadores', 'Lo más importante de un vistazo: tickets activos, sin atender, tiempo de resolución y prioridad urgente.', 'bottom'),
    step(card('Tickets por estado'), 'Tickets por estado', 'Cuántos tickets pasaron a cada estado por día. Toca un estado arriba de la gráfica para ocultarlo o mostrarlo y comparar. Pasa el cursor para ver el detalle del día.', 'top'),
    step(card('Tickets creados y resueltos'), 'Creados y resueltos', 'Compara lo que llega contra lo que se resuelve. Cambia el periodo con los botones de la derecha.', 'top'),
    step(card('Tickets por categoría'), 'Por categoría', 'Qué tipo de problema llega más.', 'top'),
    step(card('Satisfacción del servicio'), 'Satisfacción', 'Las calificaciones que dan los usuarios al cerrar sus tickets.', 'top'),
    step(card('Calificación a usuarios'), 'Calificación a usuarios', 'Cómo califica Soporte a los usuarios y por qué motivos.', 'top'),
    step(card('Rendimiento por técnico'), 'Por técnico', 'Tickets de cada técnico por estado.', 'top'),
    HELP,
  ],

  catalogs: () => [
    step(card('Categorías'), 'Categorías', 'Los tipos de problema que el usuario elige al levantar un ticket. Elige una para ver sus subcategorías.', 'right'),
    step(card('Grupos de aviso'), 'Grupos de aviso', 'Quién recibe correo cuando llega un ticket de cierta categoría.', 'top'),
    step(card('Ubicaciones'), 'Ubicaciones', 'Sucursales, CEDIS, corporativos y franquicias.', 'top'),
    step(card('Departamentos'), 'Departamentos', 'Cada usuario pertenece a uno. Los desactivados ya no se ofrecen al dar de alta.', 'top'),
    HELP,
  ],

  users: () => [
    step($('new-user'), 'Nuevo usuario', 'Da de alta una cuenta: nombre, correo, ubicación, departamento (obligatorio) y rol.', 'bottom', 'end'),
    step($('users-filters'), 'Filtros', 'Busca por nombre o correo y filtra por rol, ubicación o departamento.', 'bottom'),
    step($('users-table'), 'Usuarios', 'Con el lápiz editas a un usuario: sus datos, rol, departamento, contraseña o si está activo.', 'top'),
    HELP,
  ],
}

// Resuelve cada elemento ahora y omite los pasos que no están en pantalla
// (p. ej. Gestión en un ticket cerrado, o el menú cerrado en celular)
function buildSteps(routeName, ctx) {
  const tour = TOURS[routeName] ?? TOURS.home
  return tour(ctx)
    .filter(Boolean)
    .map((s) => (s.element ? { ...s, element: s.element() } : s))
    .filter((s) => !('element' in s) || isVisible(s.element))
}

export function hasTour(routeName) {
  return routeName in TOURS
}

let active = null

export function startTour({ routeName, isStaff = false, onDone } = {}) {
  active?.destroy()
  const steps = buildSteps(routeName, { isStaff })
  if (!steps.length) return
  active = driver({
    steps,
    showProgress: steps.length > 1,
    progressText: '{{current}} de {{total}}',
    nextBtnText: 'Siguiente',
    prevBtnText: 'Atrás',
    doneBtnText: 'Listo',
    closeBtnLabel: 'Cerrar',
    allowClose: true,
    smoothScroll: true,
    stagePadding: 6,
    stageRadius: 10,
    overlayColor: '#0B2879',
    overlayOpacity: 0.45,
    popoverClass: 'empack-tour',
    onDestroyed: () => {
      active = null
      onDone?.()
    },
  })
  active.drive()
}
