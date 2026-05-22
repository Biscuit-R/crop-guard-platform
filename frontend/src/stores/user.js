import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  login as loginApi,
  register as registerApi,
  getUserInfo as getUserInfoApi,
  logout as logoutApi,
  changePassword as changePasswordApi,
} from '../api/auth'
import {
  getUsers as getUsersApi,
  updateUserRole as updateUserRoleApi,
  updateUserStatus as updateUserStatusApi,
  deleteUser as deleteUserApi,
} from '../api/admin'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || sessionStorage.getItem('token') || '')
  const userInfo = ref(null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userInfo.value?.role === 'admin')

  function _setToken(t, remember) {
    token.value = t
    if (remember) {
      localStorage.setItem('token', t)
      sessionStorage.removeItem('token')
    } else {
      sessionStorage.setItem('token', t)
      localStorage.removeItem('token')
    }
  }

  async function login(loginData) {
    const res = await loginApi(loginData)
    if (res.success) {
      _setToken(res.data.token, loginData.remember)
      userInfo.value = res.data.user
    }
    return res
  }

  async function register(registerData) {
    const res = await registerApi(registerData)
    if (res.success) {
      _setToken(res.data.token, true)
      userInfo.value = res.data.user
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

  async function logout() {
    try {
      await logoutApi()
    } catch (e) {
      // 即使接口失败也清除本地状态
    }
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    sessionStorage.removeItem('token')
  }

  async function changePassword(data) {
    return await changePasswordApi(data)
  }

  // Admin 管理
  async function fetchUsers() {
    return await getUsersApi()
  }

  async function updateUserRole(userId, role) {
    return await updateUserRoleApi(userId, role)
  }

  async function updateUserStatus(userId, isActive) {
    return await updateUserStatusApi(userId, isActive)
  }

  async function deleteUser(userId) {
    return await deleteUserApi(userId)
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    isAdmin,
    login,
    register,
    fetchUserInfo,
    logout,
    changePassword,
    fetchUsers,
    updateUserRole,
    updateUserStatus,
    deleteUser,
  }
})
