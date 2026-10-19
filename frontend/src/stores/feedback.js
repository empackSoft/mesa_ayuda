import { defineStore } from 'pinia'
import { ticketsApi } from '../api/tickets'

// Tickets propios que esperan confirmación o encuesta (la ventana obligatoria los muestra)
export const useFeedbackStore = defineStore('feedback', {
  state: () => ({
    pending: [],
  }),

  actions: {
    async refresh() {
      try {
        this.pending = await ticketsApi.pendingFeedback()
      } catch {
        // Sin conexión: se intenta de nuevo en la siguiente navegación o aviso
      }
    },

    remove(ticketId) {
      this.pending = this.pending.filter((t) => t.id !== ticketId)
    },

    clear() {
      this.pending = []
    },
  },
})
