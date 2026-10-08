import request from '../utils/request'

export function sendSmsCode(phone) {
  return request({ url: '/auth/sms/send', method: 'post', data: { phone } })
}
