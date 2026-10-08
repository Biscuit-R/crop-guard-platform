import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '../src/stores/user'
import { login as loginApi, register as registerApi, logout as logoutApi } from '../src/api/auth'

vi.mock('../src/api/auth', () => ({
  login: vi.fn(),
  register: vi.fn(),
  getUserInfo: vi.fn(),
  logout: vi.fn(),
  changePassword: vi.fn(),
}))

const loginMock = vi.mocked(loginApi)
const registerMock = vi.mocked(registerApi)
const logoutMock = vi.mocked(logoutApi)

const okLogin = (token: string, username: string) => ({
  success: true,
  data: { token, user: { id: 1, username, role: 'user' } },
})

describe('user store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    sessionStorage.clear()
    vi.clearAllMocks()
  })

  it('登录成功：token 写 localStorage（记住我），userInfo 落 store', async () => {
    const store: any = useUserStore()
    loginMock.mockResolvedValue(okLogin('t1', 'alice'))

    const res = await store.login({ username: 'alice', password: 'x', remember: true })

    expect(res.success).toBe(true)
    expect(store.token).toBe('t1')
    expect(store.isLoggedIn).toBe(true)
    expect(store.userInfo.username).toBe('alice')
    expect(localStorage.getItem('token')).toBe('t1')
    expect(sessionStorage.getItem('token')).toBeNull()
  })

  it('登录成功（不记住）：token 写 sessionStorage', async () => {
    const store: any = useUserStore()
    loginMock.mockResolvedValue(okLogin('t2', 'alice'))

    await store.login({ username: 'alice', password: 'x', remember: false })

    expect(sessionStorage.getItem('token')).toBe('t2')
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('登录失败：不写任何 token', async () => {
    const store: any = useUserStore()
    loginMock.mockResolvedValue({ success: false } as any)

    await store.login({ username: 'alice', password: 'x' })

    expect(store.token).toBe('')
    expect(store.isLoggedIn).toBe(false)
    expect(localStorage.getItem('token')).toBeNull()
    expect(sessionStorage.getItem('token')).toBeNull()
  })

  it('注册成功：token 始终持久化到 localStorage', async () => {
    const store: any = useUserStore()
    registerMock.mockResolvedValue({
      success: true,
      data: { token: 't3', user: { id: 2, username: 'bob', role: 'user' } },
    })

    await store.register({ username: 'bob', password: 'x', phone: '13800000001' })

    expect(localStorage.getItem('token')).toBe('t3')
    expect(store.userInfo.username).toBe('bob')
  })

  it('登出：调用 API 并清空本地状态', async () => {
    localStorage.setItem('token', 't1')
    const store: any = useUserStore()
    store.token = 't1'
    store.userInfo = { id: 1, username: 'alice', role: 'user' }
    logoutMock.mockResolvedValue({ success: true })

    await store.logout()

    expect(logoutMock).toHaveBeenCalled()
    expect(store.token).toBe('')
    expect(store.userInfo).toBeNull()
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('isAdmin：role=admin 才为真', () => {
    const store: any = useUserStore()
    store.userInfo = { id: 1, username: 'a', role: 'admin' }
    expect(store.isAdmin).toBe(true)
    store.userInfo = { id: 2, username: 'b', role: 'user' }
    expect(store.isAdmin).toBe(false)
  })
})
