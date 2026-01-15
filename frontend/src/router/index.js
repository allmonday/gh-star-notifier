import { createRouter, createMemoryHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('../pages/IndexPage.vue')
  }
]

const router = createRouter({
  scrollBehavior: () => ({ top: 0 }),
  routes,
  history: createMemoryHistory()
})

export default router

