import request from '../utils/request'

// RAG 对话式问答（入口②）：症状描述 → 检索 → LLM 生成，带三档 mode。
// session_id 首次不传由后端生成并随响应返回，续问带回即可获得短期记忆。
export function ask(question, sessionId) {
  return request({
    url: '/rag/ask',
    method: 'post',
    data: { question, ...(sessionId ? { session_id: sessionId } : {}) },
  })
}
