import { createRouter, createWebHistory } from 'vue-router'

// 老版路由结构；未迁移的页面（看板/讨论区/高级功能/用户管理/短信演示）不在表内。
const routes = [
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/login',
    name: 'Login',
    meta: { title: '登录' },
    component: () => import('../views/LoginPage.vue'),
  },
  {
    path: '/register',
    name: 'Register',
    meta: { title: '注册' },
    component: () => import('../views/RegisterPage.vue'),
  },
  {
    path: '/detection',
    name: 'Detection',
    meta: { title: '虫害检测' },
    component: () => import('../views/DetectionPage.vue'),
  },
  {
    path: '/history',
    name: 'History',
    meta: { title: '检测历史' },
    component: () => import('../views/HistoryPage.vue'),
  },
  {
    path: '/guide',
    name: 'PestGuide',
    meta: { title: '虫害图鉴' },
    component: () => import('../views/PestGuidePage.vue'),
  },
  {
    path: '/qa',
    name: 'Qa',
    meta: { title: '知识问答' },
    component: () => import('../views/QaPage.vue'),
  },
  {
    path: '/profile',
    name: 'Profile',
    meta: { title: '个人中心' },
    component: () => import('../views/ProfilePage.vue'),
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    meta: { title: '页面不存在' },
    component: () => import('../views/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token') || sessionStorage.getItem('token')
  const authPaths = ['/login', '/register']

  if (authPaths.includes(to.path)) {
    next()
  } else if (!token) {
    next('/login')
  } else {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      if (payload.exp * 1000 < Date.now()) {
        localStorage.removeItem('token')
        sessionStorage.removeItem('token')
        next('/login')
        return
      }
    } catch {
      localStorage.removeItem('token')
      sessionStorage.removeItem('token')
      next('/login')
      return
    }
    next()
  }
})

export default router
