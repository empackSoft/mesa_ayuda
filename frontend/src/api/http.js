import axios from 'axios'

export const TOKEN_KEY = 'mesa_token'

const http = axios.create({
  baseURL: '/mesa_ayuda/api',
  timeout: 20000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Si el token venció o es inválido, se avisa a la app para cerrar sesión
let onUnauthorized = null

export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler
}

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const isLogin = error.config?.url?.includes('/auth/login')
    if (error.response?.status === 401 && !isLogin && onUnauthorized) {
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
