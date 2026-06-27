import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Splash', component: () => import('../views/SplashPage.vue') },
  { path: '/login', name: 'Login', component: () => import('../views/LoginPage.vue') },
  {
    path: '/app',
    component: () => import('../views/MainLayout.vue'),
    redirect: '/app/home',
    meta: { requiresAuth: true },
    children: [
      { path: 'home', name: 'Home', meta: { title: '首页' }, component: () => import('../views/HomePage.vue') },
      { path: 'entry', name: 'Entry', meta: { title: '车辆入场' }, component: () => import('../views/EntryPage.vue') },
      { path: 'pay', name: 'Pay', meta: { title: '停车缴费' }, component: () => import('../views/PayPage.vue') },
      { path: 'exit', name: 'Exit', meta: { title: '车辆出场' }, component: () => import('../views/ExitPage.vue') },
      { path: 'membership', name: 'Membership', meta: { title: '会员中心' }, component: () => import('../views/MembershipPage.vue') },
      { path: 'wallet', name: 'Wallet', meta: { title: '我的钱包' }, component: () => import('../views/WalletPage.vue') },
      { path: 'blacklist', name: 'Blacklist', meta: { title: '黑名单管理', requiresAdmin: true }, component: () => import('../views/BlacklistPage.vue') },
      { path: 'admin', name: 'Admin', meta: { title: '管理后台', requiresAdmin: true }, component: () => import('../views/AdminPage.vue') },
    ]
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')

  if (to.matched.some(r => r.meta.requiresAuth)) {
    if (!token) {
      return next('/login')
    }
    if (to.meta.requiresAdmin) {
      try {
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        if (user.role !== 'admin') {
          return next(false)
        }
      } catch { return next('/login') }
    }
  }

  if (to.path === '/login' && token) {
    return next('/app/home')
  }

  next()
})

export default router
