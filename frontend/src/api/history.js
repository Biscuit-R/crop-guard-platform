import request from '../utils/request'

// 新后端记录 → 老版历史记录形状的字段映射。
// status: 新后端 pending/done/failed → 老页面 completed/processing/failed
// 原图/结果图通过回源端点取（带 Authorization 的 img 标签拿不到 header ——
// 由 fetchImage 转 blob URL，见下方 fetchImage）。

function mapRecord(r) {
  const statusMap = { done: 'completed', pending: 'processing', failed: 'failed' }
  // 后端 box 是 {class_name, confidence, bbox:[x1,y1,x2,y2]}；
  // 老页面详情表直接消费 row.x1/y1/x2/y2，这里摊平（保留 bbox 供其他消费方）
  const boxes = (r.detections || []).map((d) => ({
    ...d,
    x1: d.bbox?.[0],
    y1: d.bbox?.[1],
    x2: d.bbox?.[2],
    y2: d.bbox?.[3],
  }))
  return {
    id: r.id,
    filename: `检测记录 #${r.id}`,
    media_type: 'image',
    status: statusMap[r.status] || r.status,
    total_objects: (r.detections || []).length,
    // 新后端未记录真实推理耗时；老页面渲染「耗时 Xs」，空值由页面 v-if 隐藏
    detection_time: null,
    created_at: r.created_at,
    model_name: r.model_name || '102',
    boxes,
    error: r.error,
    original_image: null, // 由 fetchImage 异步填充
    result_image: null,
  }
}

// img 标签带不了 Authorization header，用 fetch + blob URL 回源
async function fetchImage(recordId, variant) {
  const token = localStorage.getItem('token') || sessionStorage.getItem('token')
  const resp = await fetch(`/api/detections/${recordId}/image?variant=${variant}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!resp.ok) return null
  const blob = await resp.blob()
  return URL.createObjectURL(blob)
}

export async function getHistoryList(params) {
  const hasFilter = params.keyword || params.status
  let records
  let total
  if (hasFilter) {
    // 新后端无筛选参数：拉近期数据在客户端过滤（演示规模下够用，接口对齐后移除）
    const res = await request({
      url: '/detections', method: 'get', params: { page: 1, page_size: 100 },
    })
    records = res.items.map(mapRecord)
    if (params.keyword) {
      records = records.filter((r) => r.filename.includes(params.keyword))
    }
    if (params.status) {
      records = records.filter((r) => r.status === params.status)
    }
    total = records.length
  } else {
    const res = await request({
      url: '/detections',
      method: 'get',
      params: { page: params.page, page_size: params.page_size },
    })
    records = res.items.map(mapRecord)
    total = res.total
  }
  for (const r of records) {
    r.original_image = await fetchImage(r.id, 'original')
    r.result_image = await fetchImage(r.id, 'result')
  }
  return { success: true, data: records, total }
}

export async function getHistoryDetail(id) {
  const record = await request({ url: `/detections/${id}`, method: 'get' })
  const mapped = mapRecord(record)
  mapped.original_image = await fetchImage(id, 'original')
  mapped.result_image = await fetchImage(id, 'result')
  return mapped
}

export async function deleteHistory(id) {
  await request({ url: `/detections/${id}`, method: 'delete' })
  return { success: true, message: '删除成功' }
}

// 新后端无批量端点：逐条删
export async function batchDeleteHistory(ids) {
  for (const id of ids) {
    await request({ url: `/detections/${id}`, method: 'delete' })
  }
  return { success: true, message: `已删除 ${ids.length} 条记录` }
}
