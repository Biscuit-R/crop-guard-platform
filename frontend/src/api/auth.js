import request from '../utils/request'

// 后端形状：POST /auth/* → { token, user: {id, username, role} }；
// 这里包一层老版页面的 {success, data} 信封，页面代码不用动。

export function login(data) {
  return request({ url: '/auth/login', method: 'post', data }).then((res) => ({
    success: true,
    data: { token: res.token, user: res.user },
  }))
}

export function register(data) {
  return request({ url: '/auth/register', method: 'post', data }).then((res) => ({
    success: true,
    data: { token: res.token, user: res.user },
  }))
}

export function getUserInfo() {
  return request({ url: '/auth/me', method: 'get' }).then((res) => ({
    success: true,
    data: res,
  }))
}

export function logout() {
  return request({ url: '/auth/logout', method: 'post' }).then(() => ({ success: true }))
}

// 新后端字段名是 old_password / new_password（老页面发的是 current_password）
export function changePassword(data) {
  return request({
    url: '/auth/password',
    method: 'post',
    data: {
      old_password: data.current_password,
      new_password: data.new_password,
    },
  }).then(() => ({ success: true }))
}
