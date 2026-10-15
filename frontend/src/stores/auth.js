import { defineStore } from 'pinia'
import http, { TOKEN_KEY } from '../api/http'

const USER_KEY = 'mesa_user'

function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY))
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY),
    user: readStoredUser(),
    verified: false,
  }),

  getters: {
    isAuthenticated: (state) => Boolean(state.token && state.user),
    role: (state) => state.user?.role ?? null,
    isStaff: (state) => ['support', 'admin'].includes(state.user?.role),
    isAdmin: (state) => state.user?.role === 'admin',
  },

  actions: {
    async login(email, password) {
      const { data } = await http.post('/auth/login', { email, password })
      this.token = data.access_token
      this.user = {
        id: data.user_id,
        name: data.name,
        email: data.email,
        role: data.role,
      }
      this.verified = true
      localStorage.setItem(TOKEN_KEY, this.token)
      localStorage.setItem(USER_KEY, JSON.stringify(this.user))
    },

    // Al recargar la página, confirma con el backend que el token sigue vigente
    async verify() {
      if (!this.token || this.verified) return
      try {
        const { data } = await http.get('/auth/me')
        this.user = data
        localStorage.setItem(USER_KEY, JSON.stringify(data))
        this.verified = true
      } catch {
        this.logout()
      }
    },

    logout() {
      this.token = null
      this.user = null
      this.verified = false
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    },
  },
})
