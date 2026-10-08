import request from '../utils/request'

// 我的页统计卡。字段与老版后端一致（total_detections/total_objects/success_rate/active_days），
// 数据源是新端点 GET /detections/stats/summary。
export function getDashboardStats() {
  return request({ url: '/detections/stats/summary', method: 'get' })
}
