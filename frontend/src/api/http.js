import axios from 'axios'

// La sesión viaja en una cookie httpOnly que pone el backend al iniciar sesión:
// el frontend nunca ve ni guarda el token (un XSS no podría robarlo).
const http = axios.create({
  baseURL: '/mesa_ayuda/api',
  timeout: 20000,
  withCredentials: true,
  // El backend exige este encabezado en peticiones que modifican algo (protección CSRF)
  headers: { 'X-Requested-With': 'XMLHttpRequest' },
})

// Si la sesión venció o es inválida, se avisa a la app para cerrar sesión
let onUnauthorized = null

export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler
}

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = error.config?.url ?? ''
    const isAuthCall = url.includes('/auth/login') || url.includes('/auth/me')
    if (error.response?.status === 401 && !isAuthCall && onUnauthorized) {
      onUnauthorized()
    }
    return Promise.reject(error)
  },
)

// Mensaje legible a partir del error de FastAPI ({detail: "..."} o lista de validación)
export function errorMessage(error, fallback = 'Ocurrió un error, intenta de nuevo') {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
  if (error?.code === 'ECONNABORTED') return 'El servidor tardó demasiado en responder'
  if (!error?.response) return 'No hay conexión con el servidor'
  return fallback
}

export default http
