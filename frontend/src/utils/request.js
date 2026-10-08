import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
})

service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token') || sessionStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

service.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      sessionStorage.removeItem('token')
      router.push('/login')
      return Promise.reject(error)
    }
    ElMessage.error('请求失败：' + _readableDetail(error.response?.data))
    return Promise.reject(error)
  },
)

// FastAPI 校验错误（422）的 detail 是数组 [{loc, msg, ...}]，直接拼会变 [object Object]；
// 拍平成「字段: 消息」串，其他接口的 string detail 原样透出
function _readableDetail(data) {
  const detail = data?.detail
  if (typeof detail === 'string') return detail || data?.message || '服务器错误'
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const field = (d.loc || []).filter((p) => p !== 'body').join('.')
        return field ? `${field}: ${d.msg}` : d.msg
      })
      .join('；')
  }
  return data?.message || '服务器错误'
}

export default service
