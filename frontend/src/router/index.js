/**
 * router/index.js — Vue Router configuration
 *
 * Navigation guard redirects unauthenticated users to /login.
 * All routes except /login require a valid JWT in localStorage.
 */

import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    redirect: '/jobs',
  },
  {
    path: '/jobs',
    name: 'Jobs',
    component: () => import('../views/JobsListView.vue'),
  },
  {
    path: '/jobs/new',
    name: 'JobCreate',
    component: () => import('../views/JobCreateView.vue'),
  },
  {
    path: '/jobs/:id',
    name: 'JobDetail',
    component: () => import('../views/JobDetailView.vue'),
    props: true,
  },
  {
    path: '/dispatch',
    name: 'Dispatch',
    component: () => import('../views/DispatchBoardView.vue'),
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFoundView.vue'),
    meta: { public: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard — redirect to login if no token
router.beforeEach((to) => {
  const token = localStorage.getItem('hvac-token')
  if (!to.meta.public && !token) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'Login' && token) {
    return { name: 'Jobs' }
  }
})

export default router
