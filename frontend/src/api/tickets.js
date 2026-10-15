import http from './http'

// Llamadas a la API de tickets y catálogos que usan las vistas

export const ticketsApi = {
  list: (params) => http.get('/tickets/', { params }).then((r) => r.data),
  get: (id) => http.get(`/tickets/${id}`).then((r) => r.data),
  create: (payload) => http.post('/tickets/', payload).then((r) => r.data),
  update: (id, payload) => http.put(`/tickets/${id}`, payload).then((r) => r.data),
  assign: (id, userId) =>
    http.patch(`/tickets/${id}/assign`, { assigned_to_user_id: userId }).then((r) => r.data),
  changeStatus: (id, status) => http.patch(`/tickets/${id}/status`, { status }).then((r) => r.data),
  close: (id) => http.patch(`/tickets/${id}/close`).then((r) => r.data),

  // El backend responde 404 cuando aún no hay historial; se trata como lista vacía
  history: (id) =>
    http
      .get(`/tickets/${id}/history`)
      .then((r) => r.data)
      .catch((e) => {
        if (e.response?.status === 404) return []
        throw e
      }),

  comments: (id) => http.get(`/tickets/${id}/comments`).then((r) => r.data),
  addComment: (id, body, isInternal) =>
    http.post(`/tickets/${id}/comments`, { body, is_internal: isInternal }).then((r) => r.data),

  attachments: (id) => http.get(`/tickets/${id}/attachments`).then((r) => r.data),
  uploadAttachment: (id, file) => {
    const data = new FormData()
    data.append('file', file)
    // timeout más largo: los archivos pueden pesar hasta 10 MB
    return http.post(`/tickets/${id}/attachment`, data, { timeout: 120000 }).then((r) => r.data)
  },
  // La descarga requiere el token, así que se pide como blob en vez de un <a href>
  downloadAttachment: (id, attachmentId) =>
    http
      .get(`/tickets/${id}/attachments/${attachmentId}`, { responseType: 'blob', timeout: 120000 })
      .then((r) => r.data),
}

export const catalogApi = {
  incidencias: () => http.get('/incidencias/active').then((r) => r.data),
  subincidencias: (incidenciaId) =>
    http.get(`/incidencias/${incidenciaId}/subincidencias`).then((r) => r.data),
}

export const usersApi = {
  staff: () => http.get('/users/staff').then((r) => r.data),
}
