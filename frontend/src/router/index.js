import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

import MainLayout from '../layouts/MainLayout.vue'
import LoginView from '../views/LoginView.vue'

const STAFF = ['support', 'admin']

const routes = [
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { public: true },
  },
  {
    // "Olvidé mi contraseña" y link del correo (?token=…)
    path: '/restablecer-contrasena',
    name: 'password-reset',
    component: () => import('../views/PasswordResetView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'home',
        component: () => import('../views/HomeView.vue'),
      },
      {
        path: 'tickets',
        name: 'tickets',
        component: () => import('../views/TicketsView.vue'),
        meta: { title: 'Tickets' },
      },
      {
        path: 'tickets/:id',
        name: 'ticket-detail',
        component: () => import('../views/TicketDetailView.vue'),
        meta: { title: 'Detalle de ticket' },
      },
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('../views/DashboardView.vue'),
        meta: { title: 'Dashboard', roles: STAFF },
      },
      {
        path: 'catalogos',
        name: 'catalogs',
        component: () => import('../views/CatalogsView.vue'),
        meta: { title: 'Catálogos', roles: ['admin'] },
      },
      {
        path: 'usuarios',
        name: 'users',
        component: () => import('../views/UsersView.vue'),
        meta: { title: 'Usuarios', roles: ['admin'] },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('../views/NotFoundView.vue'),
    meta: { public: true },
  },
]

const router = createRouter({
  history: createWebHistory('/mesa_ayuda/'),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (to.meta.public) {
    if (to.name === 'login' && auth.isAuthenticated) return { name: 'home' }
    return true
  }

  await auth.verify()

  if (!auth.isAuthenticated) {
    // Se guarda a dónde iba (ej. link de un correo) para regresar tras el login
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  const roles = to.matched.flatMap((r) => r.meta.roles ?? [])
  if (roles.length && !roles.includes(auth.role)) {
    return { name: 'home' }
  }

  return true
})

export default router
