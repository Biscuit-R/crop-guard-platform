import request from '../utils/request'

export function getUsers() {
  return request({ url: '/admin/users', method: 'get' })
}

export function updateUserRole(userId, role) {
  return request({ url: `/admin/users/${userId}/role`, method: 'put', data: { role } })
}

export function updateUserStatus(userId, isActive) {
  return request({ url: `/admin/users/${userId}/status`, method: 'put', data: { is_active: isActive } })
}

export function deleteUser(userId) {
  return request({ url: `/admin/users/${userId}`, method: 'delete' })
}
