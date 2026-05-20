import request from '../utils/request'

export function getHistoryList(params) {
  return request({
    url: '/history/list',
    method: 'get',
    params
  })
}

export function getHistoryDetail(id) {
  return request({
    url: `/history/${id}`,
    method: 'get'
  })
}

export function deleteHistory(id) {
  return request({
    url: `/history/${id}`,
    method: 'delete'
  })
}
