import request from '../utils/request'

export const detectSingleImage = (data) => {
  return request({
    url: '/detection/single',
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const getPestList = () => {
  return request({
    url: '/detection/pests/list',
    method: 'get'
  })
}
