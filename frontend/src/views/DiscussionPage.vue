<template>
  <div class="discussion-page">
    <div class="page-header">
      <h1 class="page-title">讨论区</h1>
      <p class="page-subtitle">分享图片、交流学习病虫害知识</p>
    </div>

    <div class="discussion-layout">
      <!-- 左侧导航 -->
      <aside class="side-nav">
        <div
          class="side-nav-item"
          :class="{ active: activeTab === 'pinned' }"
          @click="switchTab('pinned')"
        >
          <el-icon><Star /></el-icon>
          <span>精选</span>
        </div>
        <div
          class="side-nav-item"
          :class="{ active: activeTab === 'all' }"
          @click="switchTab('all')"
        >
          <el-icon><ChatLineSquare /></el-icon>
          <span>全部讨论</span>
        </div>
        <div
          v-if="userStore.isAdmin"
          class="side-nav-item"
          :class="{ active: activeTab === 'pending' }"
          @click="switchTab('pending')"
        >
          <el-icon><Document /></el-icon>
          <span>待审核</span>
          <span v-if="pendingCount > 0" class="side-badge">{{ pendingCount }}</span>
        </div>
      </aside>

      <!-- 右侧内容 -->
      <div class="main-content">
        <div class="action-bar">
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            发布帖子
          </el-button>
        </div>

        <div class="post-list" v-loading="loading">
          <div
            v-for="post in posts"
            :key="post.id"
            class="post-card"
            :class="{ pinned: post.is_pinned }"
            @click="openPostDetail(post)"
          >
            <div class="post-image" v-if="post.image_url">
              <img :src="post.image_url" alt="帖子图片" />
            </div>
            <div class="post-content">
              <div class="post-title-row">
                <span v-if="post.is_pinned" class="pin-badge">
                  <el-icon><Star /></el-icon> 精选
                </span>
                <p class="post-text">{{ post.content }}</p>
              </div>
              <div class="post-meta">
                <span class="meta-author">
                  <el-icon><User /></el-icon>
                  {{ post.username }}
                </span>
                <span class="meta-time">
                  <el-icon><Clock /></el-icon>
                  {{ formatTime(post.created_at) }}
                </span>
                <span class="meta-comments">
                  <el-icon><ChatDotRound /></el-icon>
                  {{ post.comment_count }} 评论
                </span>
              </div>
            </div>
            <div v-if="activeTab === 'pending'" class="post-status-badge pending">待审核</div>
            <div v-else-if="post.status === 'rejected'" class="post-status-badge rejected">已拒绝</div>
            <el-button
              v-if="canDelete(post)"
              class="post-delete-btn"
              type="danger"
              :icon="Delete"
              circle
              size="small"
              @click.stop="handleDelete(post)"
            />
          </div>
        </div>

        <div v-if="!loading && posts.length === 0" class="empty-state">
          <el-icon :size="64" class="empty-icon"><ChatLineSquare /></el-icon>
          <p class="empty-text">
            {{ activeTab === 'pending' ? '暂无待审核帖子' : activeTab === 'pinned' ? '暂无精选帖子' : '暂无帖子，来发布第一条吧' }}
          </p>
        </div>

        <div class="pagination-wrap" v-if="total > pageSize">
          <el-pagination
            background
            layout="prev, pager, next"
            :total="total"
            :page-size="pageSize"
            :current-page="currentPage"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </div>

    <!-- 创建帖子弹窗 -->
    <el-dialog v-model="showCreateDialog" title="发布帖子" width="520px" :close-on-click-modal="false">
      <el-form :model="createForm" label-position="top">
        <el-form-item label="内容" required>
          <el-input
            v-model="createForm.content"
            type="textarea"
            :rows="4"
            placeholder="分享你的发现或提问..."
            maxlength="5000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="图片（可选）">
          <el-upload
            class="image-uploader"
            :auto-upload="false"
            :show-file-list="true"
            :limit="1"
            accept="image/*"
            :on-change="handleImageChange"
            :on-remove="() => createForm.image = null"
          >
            <el-button size="small">
              <el-icon><Upload /></el-icon>
              选择图片
            </el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitPost">发布</el-button>
      </template>
    </el-dialog>

    <!-- 帖子详情弹窗 -->
    <el-dialog v-model="showDetailDialog" title="帖子详情" width="600px" :close-on-click-modal="true">
      <div v-if="currentPost" class="post-detail">
        <div class="detail-image" v-if="currentPost.image_url">
          <img :src="currentPost.image_url" alt="帖子图片" />
        </div>
        <div class="detail-header">
          <span v-if="currentPost.is_pinned" class="pin-badge large">
            <el-icon><Star /></el-icon> 精选
          </span>
        </div>
        <p class="detail-content">{{ currentPost.content }}</p>
        <div class="detail-meta">
          <span><el-icon><User /></el-icon> {{ currentPost.username }}</span>
          <span><el-icon><Clock /></el-icon> {{ formatTime(currentPost.created_at) }}</span>
        </div>

        <!-- 管理员操作 -->
        <div v-if="userStore.isAdmin" class="admin-actions">
          <template v-if="currentPost.status === 'pending'">
            <el-button type="success" size="small" @click="handleReview('approved')">通过</el-button>
            <el-button type="danger" size="small" @click="handleReview('rejected')">拒绝</el-button>
          </template>
          <el-button
            v-if="currentPost.status === 'approved'"
            size="small"
            :type="currentPost.is_pinned ? 'warning' : 'primary'"
            @click="handleTogglePin"
          >
            <el-icon><Star /></el-icon>
            {{ currentPost.is_pinned ? '取消精选' : '设为精选' }}
          </el-button>
          <el-button
            type="danger"
            size="small"
            @click="handleDelete(currentPost)"
          >
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
        </div>

        <!-- 用户删除自己的帖子 -->
        <div v-if="!userStore.isAdmin && canDelete(currentPost)" class="user-actions">
          <el-button type="danger" size="small" @click="handleDelete(currentPost)">
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
        </div>

        <div class="comments-section">
          <h4 class="comments-title">评论 ({{ currentPost.comments?.length || 0 }})</h4>
          <div class="comments-list">
            <div v-for="comment in currentPost.comments" :key="comment.id" class="comment-item">
              <div class="comment-header">
                <span class="comment-author">{{ comment.username }}</span>
                <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
              </div>
              <p class="comment-text">{{ comment.content }}</p>
            </div>
            <div v-if="!currentPost.comments?.length" class="no-comments">暂无评论</div>
          </div>
          <div class="comment-input">
            <el-input
              v-model="newComment"
              placeholder="写下你的评论..."
              maxlength="2000"
              @keyup.enter="submitComment"
            >
              <template #append>
                <el-button @click="submitComment" :loading="commenting">发送</el-button>
              </template>
            </el-input>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, User, Clock, ChatDotRound, ChatLineSquare, Upload, Star, Document, Delete,
} from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import {
  getForumPosts, createForumPost, getForumPostDetail,
  createForumComment, getAdminForumPosts, reviewForumPost, togglePinPost,
  deleteForumPost, adminDeleteForumPost,
} from '../api/forum'

const userStore = useUserStore()

const activeTab = ref('all')
const loading = ref(false)
const submitting = ref(false)
const commenting = ref(false)
const posts = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 10
const pendingCount = ref(0)

const showCreateDialog = ref(false)
const createForm = ref({ content: '', image: null })

const showDetailDialog = ref(false)
const currentPost = ref(null)
const newComment = ref('')

function formatTime(timeStr) {
  if (!timeStr) return ''
  const d = new Date(timeStr)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function switchTab(tab) {
  activeTab.value = tab
  currentPage.value = 1
  if (tab === 'pending') loadAdminPosts()
  else loadPosts()
}

async function loadPosts() {
  loading.value = true
  try {
    const pinnedOnly = activeTab.value === 'pinned'
    const res = await getForumPosts(currentPage.value, pageSize, pinnedOnly)
    if (res.success) {
      posts.value = res.data
      total.value = res.total
    }
  } catch { /* ignore */ }
  loading.value = false
}

async function loadAdminPosts() {
  loading.value = true
  try {
    const res = await getAdminForumPosts(currentPage.value, pageSize, 'pending')
    if (res.success) {
      posts.value = res.data
      total.value = res.total
    }
  } catch { /* ignore */ }
  loading.value = false
}

async function loadPendingCount() {
  if (!userStore.isAdmin) return
  try {
    const res = await getAdminForumPosts(1, 1, 'pending')
    if (res.success) pendingCount.value = res.total
  } catch { /* ignore */ }
}

function handlePageChange(page) {
  currentPage.value = page
  if (activeTab.value === 'pending') loadAdminPosts()
  else loadPosts()
}

function handleImageChange(file) {
  createForm.value.image = file.raw
}

async function submitPost() {
  if (!createForm.value.content.trim()) {
    ElMessage.warning('请输入内容')
    return
  }
  submitting.value = true
  try {
    const formData = new FormData()
    formData.append('content', createForm.value.content)
    if (createForm.value.image) {
      formData.append('image', createForm.value.image)
    }
    const res = await createForumPost(formData)
    if (res.success) {
      ElMessage.success('发布成功，等待管理员审核')
      showCreateDialog.value = false
      createForm.value = { content: '', image: null }
    }
  } catch { /* ignore */ }
  submitting.value = false
}

async function openPostDetail(post) {
  try {
    const res = await getForumPostDetail(post.id)
    if (res.success) {
      currentPost.value = res.data
      showDetailDialog.value = true
    }
  } catch { /* ignore */ }
}

async function submitComment() {
  if (!newComment.value.trim() || !currentPost.value) return
  commenting.value = true
  try {
    const res = await createForumComment(currentPost.value.id, newComment.value)
    if (res.success) {
      ElMessage.success('评论成功')
      newComment.value = ''
      const detail = await getForumPostDetail(currentPost.value.id)
      if (detail.success) currentPost.value = detail.data
    }
  } catch { /* ignore */ }
  commenting.value = false
}

async function handleReview(status) {
  if (!currentPost.value) return
  try {
    const res = await reviewForumPost(currentPost.value.id, status)
    if (res.success) {
      ElMessage.success(res.message)
      showDetailDialog.value = false
      loadAdminPosts()
      loadPendingCount()
    }
  } catch { /* ignore */ }
}

async function handleTogglePin() {
  if (!currentPost.value) return
  try {
    const res = await togglePinPost(currentPost.value.id)
    if (res.success) {
      ElMessage.success(res.message)
      currentPost.value.is_pinned = res.data.is_pinned
      // refresh list
      if (activeTab.value === 'pending') loadAdminPosts()
      else loadPosts()
    }
  } catch { /* ignore */ }
}

function canDelete(post) {
  if (!post) return false
  return userStore.isAdmin || post.username === userStore.userInfo?.username
}

async function handleDelete(post) {
  try {
    await ElMessageBox.confirm('确定要删除这条帖子吗？此操作不可撤销。', '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch { return }

  try {
    const res = userStore.isAdmin
      ? await adminDeleteForumPost(post.id)
      : await deleteForumPost(post.id)
    if (res.success) {
      ElMessage.success('帖子已删除')
      showDetailDialog.value = false
      if (activeTab.value === 'pending') loadAdminPosts()
      else loadPosts()
      loadPendingCount()
    }
  } catch { /* ignore */ }
}

onMounted(() => {
  loadPosts()
  loadPendingCount()
})
</script>

<style scoped>
.discussion-page {
  width: 100%;
  max-width: 1040px;
  margin: 0 auto;
  padding-bottom: 24px;
}

/* === 页头 === */
.page-header {
  margin-bottom: 20px;
  animation: fade-up 0.6s var(--ease-out-expo) both;
}
.page-title {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 6px;
  letter-spacing: -0.02em;
}
.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

/* === 双栏布局 === */
.discussion-layout {
  display: flex;
  gap: 20px;
  animation: fade-up 0.6s var(--ease-out-expo) both;
  animation-delay: 0.1s;
}

/* === 左侧导航 === */
.side-nav {
  width: 140px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  position: sticky;
  top: 24px;
  align-self: flex-start;
}
.side-nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 14px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--ease-out-expo);
  background: var(--surface);
  border: 1px solid transparent;
  box-shadow: var(--card-shadow);
}
.side-nav-item:hover {
  background: var(--primary-light);
  color: var(--text-primary);
}
.side-nav-item.active {
  background: var(--primary-color);
  color: #ffffff;
  font-weight: 500;
  box-shadow: var(--card-shadow-hover);
}
.side-badge {
  margin-left: auto;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: #ef4444;
  color: #ffffff;
  font-size: 11px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* === 右侧主内容 === */
.main-content {
  flex: 1;
  min-width: 0;
}

/* === 操作栏 === */
.action-bar {
  margin-bottom: 16px;
}

/* === 帖子列表 === */
.post-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.post-card {
  display: flex;
  gap: 16px;
  background: var(--surface);
  border-radius: 14px;
  padding: 16px;
  box-shadow: var(--card-shadow);
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: box-shadow 0.3s var(--ease-out-expo), transform 0.3s var(--ease-out-expo), border-color 0.2s ease;
  position: relative;
  overflow: hidden;
}
.post-card:hover {
  box-shadow: var(--card-shadow-hover);
  transform: translateY(-2px);
}
.post-card.pinned {
  border-color: var(--primary-color);
  background: linear-gradient(135deg, var(--surface) 0%, rgba(180, 83, 9, 0.03) 100%);
}
.post-image {
  width: 100px;
  height: 100px;
  flex-shrink: 0;
  border-radius: 10px;
  overflow: hidden;
}
.post-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.post-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.post-title-row {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  flex-wrap: wrap;
}
.post-text {
  font-size: 14px;
  color: var(--text-primary);
  margin: 0 0 8px 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.5;
}
.pin-badge {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 1px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  background: rgba(180, 83, 9, 0.1);
  color: var(--primary-color);
  flex-shrink: 0;
  margin-bottom: 6px;
}
.pin-badge.large {
  font-size: 13px;
  padding: 3px 10px;
}
.post-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-secondary);
}
.meta-author, .meta-time, .meta-comments {
  display: flex;
  align-items: center;
  gap: 4px;
}
.post-status-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
}
.post-status-badge.pending {
  background: #fef3c7;
  color: #92400e;
}
.post-status-badge.rejected {
  background: #fee2e2;
  color: #991b1b;
}

/* === 空状态 === */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background: var(--surface);
  border-radius: 14px;
  box-shadow: var(--card-shadow);
  border: 1px solid var(--border-color);
}
.empty-icon {
  color: var(--primary-color);
  margin-bottom: 16px;
  opacity: 0.5;
}
.empty-text {
  font-size: 15px;
  color: var(--text-secondary);
  margin: 0;
}

/* === 分页 === */
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

/* === 弹窗样式 === */
.image-uploader {
  width: 100%;
}

.post-detail .detail-header {
  margin-bottom: 8px;
}
.post-detail .detail-image {
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 12px;
  max-height: 400px;
}
.post-detail .detail-image img {
  width: 100%;
  height: auto;
  object-fit: contain;
}
.post-detail .detail-content {
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-primary);
  margin: 0 0 12px 0;
  white-space: pre-wrap;
  word-break: break-word;
}
.post-detail .detail-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}
.detail-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.admin-actions {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  gap: 8px;
}
.user-actions {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
}
.post-delete-btn {
  position: absolute;
  bottom: 12px;
  right: 12px;
  opacity: 0;
  transition: opacity 0.2s ease;
}
.post-card:hover .post-delete-btn {
  opacity: 1;
}

.comments-section {
  margin-top: 8px;
}
.comments-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px 0;
}
.comments-list {
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 12px;
}
.comment-item {
  padding: 10px 0;
  border-bottom: 1px solid var(--border-color);
}
.comment-item:last-child {
  border-bottom: none;
}
.comment-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}
.comment-author {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}
.comment-time {
  font-size: 12px;
  color: var(--text-secondary);
}
.comment-text {
  font-size: 14px;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}
.no-comments {
  text-align: center;
  padding: 20px;
  color: var(--text-secondary);
  font-size: 13px;
}
.comment-input {
  margin-top: 8px;
}
</style>
