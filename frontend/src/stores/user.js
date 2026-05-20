import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, register as registerApi, getUserInfo as getUserInfoApi } from '../api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)

  const isLoggedIn = computed(() => !!token.value)

  async function login(loginData) {
    const res = await loginApi(loginData)
    if (res.success) {
      token.value = res.data.token
      userInfo.value = res.data.user
      localStorage.setItem('token', res.data.token)
    }
    return res
  }

  async function register(registerData) {
    const res = await registerApi(registerData)
    if (res.success) {
      token.value = res.data.token
      userInfo.value = res.data.user
      localStorage.setItem('token', res.data.token)
    }
    return res
  }

  async function fetchUserInfo() {
    const res = await getUserInfoApi()
    if (res.success) {
      userInfo.value = res.data
    }
    return res
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    login,
    register,
    fetchUserInfo,
    logout
  }
})
