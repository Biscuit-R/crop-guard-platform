import request from '../utils/request'

// 获取帖子列表
export const getForumPosts = (page = 1, pageSize = 10, pinnedOnly = false) => {
  return request({
    url: '/forum/posts',
    method: 'get',
    params: { page, page_size: pageSize, pinned_only: pinnedOnly }
  })
}

// 创建帖子
export const createForumPost = (formData) => {
  return request({
    url: '/forum/posts',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// 获取帖子详情
export const getForumPostDetail = (id) => {
  return request({
    url: `/forum/posts/${id}`,
    method: 'get'
  })
}

// 发表评论
export const createForumComment = (postId, content) => {
  return request({
    url: `/forum/posts/${postId}/comments`,
    method: 'post',
    data: { content }
  })
}

// 管理员获取待审核帖子
export const getAdminForumPosts = (page = 1, pageSize = 10, status = 'pending') => {
  return request({
    url: '/forum/admin/posts',
    method: 'get',
    params: { page, page_size: pageSize, status }
  })
}

// 管理员审核帖子
export const reviewForumPost = (postId, status, note = '') => {
  return request({
    url: `/forum/admin/posts/${postId}/review`,
    method: 'put',
    data: { status, note }
  })
}

// 管理员置顶/取消置顶
export const togglePinPost = (postId) => {
  return request({
    url: `/forum/admin/posts/${postId}/pin`,
    method: 'put'
  })
}

// 用户删除自己的帖子
export const deleteForumPost = (postId) => {
  return request({
    url: `/forum/posts/${postId}`,
    method: 'delete'
  })
}

// 管理员删除帖子
export const adminDeleteForumPost = (postId) => {
  return request({
    url: `/forum/admin/posts/${postId}`,
    method: 'delete'
  })
}
