import request from '../utils/request'

// 新后端检测语义（D1/D12）：
// - 只有单图 POST /detections（multipart 字段名 image，不是老版的 file）
// - conf / model_name 暂无对应配置项，字段被忽略（老页面控件保留但不影响结果）
// - 结果图不在响应里 → GET /detections/{id}/image?variant=result 回源

function mapRecordToResult(record, filename) {
  // 后端 box 是 {class_name, confidence, bbox:[x1,y1,x2,y2]}；
  // 老页面部分消费方直接读 x1..y2，这里摊平（保留 bbox）
  const boxes = (record.detections || []).map((d) => ({
    ...d,
    x1: d.bbox?.[0],
    y1: d.bbox?.[1],
    x2: d.bbox?.[2],
    y2: d.bbox?.[3],
  }))
  return {
    filename: filename || '单图检测',
    total_objects: (record.detections || []).length,
    // 新后端未记录推理耗时（老页面按数字渲染「Xs」），置空由页面兜底显示 '-'
    detection_time: null,
    boxes,
    result_image_url: `/api/detections/${record.id}/image?variant=result`,
    status: record.status,
  }
}

function detectOne(file) {
  const formData = new FormData()
  formData.append('image', file)
  return request({
    url: '/detections',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  }).then((record) => {
    if (record.status === 'failed') {
      return { success: false, message: record.error || '检测失败' }
    }
    return { success: true, data: mapRecordToResult(record, file?.name) }
  })
}

export const detectSingleImage = (formData) => {
  const file = formData.get('file')
  return detectOne(file)
}

// 新后端没有批量端点：顺序逐张调单图检测，对页面呈现为同一结果结构
export const detectBatchImages = async (formData) => {
  const files = formData.getAll('files')
  const results = []
  for (const f of files) {
    results.push(await detectOne(f))
  }
  return { success: true, data: { results } }
}

export const detectVideo = () =>
  Promise.resolve({ success: false, message: '视频检测尚未迁移到新平台' })

export const detectFrame = () =>
  Promise.resolve({ success: false, message: '摄像头检测尚未迁移到新平台' })

// 模型管理属砍序切片：平台只部署一个模型（backend/models/model_102.pt），
// 这里返回真实存在的那一个，页面的模型选择区可见但只有一项
export const getModels = () =>
  Promise.resolve({
    success: true,
    data: [{ filename: 'model_102.pt', version: '102', is_current: true }],
  })

export const getModelStatus = () =>
  Promise.resolve({
    success: true,
    data: { model_version: '102', filename: 'model_102.pt', status: 'ready' },
  })

export const switchModel = () =>
  Promise.resolve({ success: false, message: '当前平台只部署了一个模型' })

// 图鉴全量（GET /rag/pests，纯内存数据）。
// 后端无 id 字段，老页面拿 pest.id 做 v-for key —— 用唯一的 name 补上
export const getPestList = () =>
  request({ url: '/rag/pests', method: 'get' }).then((data) => ({
    success: true,
    data: data.map((p) => ({ ...p, id: p.id ?? p.name })),
  }))
