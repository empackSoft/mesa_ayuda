import { defineStore } from 'pinia'
import http from '../api/http'

// Solo se guardan los datos visibles del usuario (nombre, rol) para pintar la app al recargar.
// La sesión real es la cookie httpOnly; el backend la valida en cada petición.
export const USER_KEY = 'mesa_user'

function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY))
  } catch {
    return null
  }
}

function storeUser(user) {
  try {
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user))
    else localStorage.removeItem(USER_KEY)
  } catch {
    // sin almacenamiento: la sesión sigue funcionando con la cookie
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: readStoredUser(),
    verified: false,
  }),

  getters: {
    isAuthenticated: (state) => Boolean(state.user),
    role: (state) => state.user?.role ?? null,
    isStaff: (state) => ['support', 'admin'].includes(state.user?.role),
    isAdmin: (state) => state.user?.role === 'admin',
  },

  actions: {
    async login(email, password) {
      const { data } = await http.post('/auth/login', { email, password })
      this.user = {
        id: data.user_id,
        name: data.name,
        email: data.email,
        role: data.role,
      }
      this.verified = true
      storeUser(this.user)
    },

    // Al recargar la página, confirma con el backend que la sesión sigue vigente.
    // Solo se cierra sesión si el backend la rechaza: si el servidor no responde
    // un momento (reinicio, red), se conserva y se vuelve a intentar.
    async verify() {
      if (this.verified) return
      try {
        const { data } = await http.get('/auth/me')
        this.user = data
        storeUser(data)
        this.verified = true
      } catch (e) {
        const status = e.response?.status
        if (status === 401 || status === 403) this.clear()
      }
    },

    clear() {
      this.user = null
      this.verified = false
      storeUser(null)
    },

    async logout() {
      this.clear()
      // Borra la cookie en el servidor (si falla, igual vence sola)
      await http.post('/auth/logout').catch(() => {})
    },
  },
})
