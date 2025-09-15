import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('../layouts/BasicLayout.vue'),
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue')
      },

      {
        path: '/lora-management',
        name: 'LoraManagement',
        component: () => import('../views/LoraManagement.vue')
      },
      {
        path: '/base-model-management',
        name: 'BaseModelManagement',
        component: () => import('../views/BaseModelManagement.vue')
      },
      {
        path: '/workflow-management',
        name: 'WorkflowManagement',
        component: () => import('../views/WorkflowManagement.vue')
      },
      {
        path: '/workflow-upload',
        name: 'WorkflowUpload',
        component: () => import('../views/WorkflowUpload.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router