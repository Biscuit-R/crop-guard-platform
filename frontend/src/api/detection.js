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

export const getModelStatus = () => {
  return request({ url: '/detection/model/status', method: 'get' })
}

export const getModels = () => {
  return request({ url: '/detection/models', method: 'get' })
}

export const switchModel = (version) => {
  return request({
    url: '/detection/models/switch',
    method: 'post',
    data: { version }
  })
}
