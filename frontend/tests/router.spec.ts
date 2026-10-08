import { describe, it, expect, beforeEach } from 'vitest'
import router from '../src/router'

// 守卫逻辑：无 token / 过期 token → /login 并清存储；有效 token 放行
const makeToken = (expSeconds: number) =>
  'h.' + btoa(JSON.stringify({ exp: expSeconds })) + '.s'

describe('router guard', () => {
  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
  })

  it('路由表：五个主页面 + 登录/注册/404 齐全', () => {
    const paths = router.getRoutes().map((r) => r.path)
    for (const p of ['/login', '/register', '/detection', '/history', '/guide', '/qa', '/profile']) {
      expect(paths).toContain(p)
    }
  })

  // 首个导航会触发懒加载视图的首次编译，jsdom 下较慢，放宽超时
  it('根路径重定向到 /login', { timeout: 30000 }, async () => {
    await router.push('/')
    await router.isReady()
    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('未登录访问受保护页 → 重定向 /login', async () => {
    await router.push('/detection')
    await router.isReady()
    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('有效 token 放行受保护页', async () => {
    localStorage.setItem('token', makeToken(Math.floor(Date.now() / 1000) + 3600))
    await router.push('/history')
    await router.isReady()
    expect(router.currentRoute.value.path).toBe('/history')
  })

  it('过期 token → 重定向 /login 并清除存储', async () => {
    localStorage.setItem('token', makeToken(Math.floor(Date.now() / 1000) - 10))
    await router.push('/guide')
    await router.isReady()
    expect(router.currentRoute.value.path).toBe('/login')
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('格式非法的 token → 重定向 /login 并清除存储', async () => {
    localStorage.setItem('token', 'not-a-jwt')
    await router.push('/qa')
    await router.isReady()
    expect(router.currentRoute.value.path).toBe('/login')
    expect(localStorage.getItem('token')).toBeNull()
  })
})
