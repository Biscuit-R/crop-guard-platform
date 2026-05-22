<template>
  <div class="dashboard-page">
    <div class="page-header">
      <h1 class="page-title">数据看板</h1>
      <p class="page-subtitle">实时掌握检测动态与使用统计</p>
    </div>

    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon" style="background: #0d9488">
          <el-icon :size="24" color="#ffffff"><Picture /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_detections }}</div>
          <div class="stat-label">总检测次数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #16a34a">
          <el-icon :size="24" color="#ffffff"><Aim /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_objects }}</div>
          <div class="stat-label">累计检测目标</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #3b82f6">
          <el-icon :size="24" color="#ffffff"><CircleCheck /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.success_rate }}%</div>
          <div class="stat-label">检测成功率</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #f59e0b">
          <el-icon :size="24" color="#ffffff"><Calendar /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.active_days }}</div>
          <div class="stat-label">使用天数</div>
        </div>
      </div>
    </div>

    <div class="content-row">
      <div class="announcements">
        <div class="section-card">
          <div class="section-header">
            <span class="section-title">更新公告</span>
          </div>
          <div class="announcement-list">
            <div class="announcement-item">
              <div class="announcement-dot"></div>
              <div class="announcement-content">
                <div class="announcement-title">视频检测功能上线</div>
                <div class="announcement-desc">支持上传视频进行逐帧检测，自动生成标注视频和统计摘要</div>
                <div class="announcement-time">2026-05-22</div>
              </div>
            </div>
            <div class="announcement-item">
              <div class="announcement-dot"></div>
              <div class="announcement-content">
                <div class="announcement-title">批量检测优化</div>
                <div class="announcement-desc">批量检测支持更多图片格式，检测速度提升 30%</div>
                <div class="announcement-time">2026-05-18</div>
              </div>
            </div>
            <div class="announcement-item">
              <div class="announcement-dot"></div>
              <div class="announcement-content">
                <div class="announcement-title">病虫害图鉴更新</div>
                <div class="announcement-desc">新增 12 种常见病虫害类别，覆盖更多农作物场景</div>
                <div class="announcement-time">2026-05-15</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="recent-section">
        <div class="section-card">
          <div class="section-header">
            <span class="section-title">最近检测</span>
            <el-button text type="primary" @click="$router.push('/history')">查看全部</el-button>
          </div>
          <div v-if="recentRecords.length === 0" class="empty-recent">
            <el-icon :size="48" color="#d1d5db"><Picture /></el-icon>
            <p>暂无检测记录</p>
          </div>
          <div v-else class="recent-list">
            <div v-for="record in recentRecords" :key="record.id" class="recent-item">
              <div class="recent-preview">
                <img v-if="record.result_image" :src="record.result_image" alt="结果" />
                <el-icon v-else :size="20" color="#9ca3af"><Picture /></el-icon>
              </div>
              <div class="recent-info">
                <div class="recent-name">{{ record.filename }}</div>
                <div class="recent-meta">{{ record.total_objects }} 个目标 · {{ record.created_at }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import {
  Picture, Aim, CircleCheck, Calendar,
} from "@element-plus/icons-vue";
import { getDashboardStats } from "../api/dashboard";
import { getHistoryList } from "../api/history";

const stats = reactive({
  total_detections: 0,
  total_objects: 0,
  success_rate: 0,
  active_days: 0,
});

const recentRecords = ref([]);

onMounted(async () => {
  try {
    const res = await getDashboardStats();
    if (res) {
      stats.total_detections = res.total_detections ?? 0;
      stats.total_objects = res.total_objects ?? 0;
      stats.success_rate = res.success_rate ?? 0;
      stats.active_days = res.active_days ?? 0;
    }
  } catch (e) {
    console.error("获取统计数据失败:", e);
  }

  try {
    const res = await getHistoryList({ page: 1, page_size: 5 });
    if (res.success) {
      recentRecords.value = res.data;
    }
  } catch (e) {
    console.error("获取最近记录失败:", e);
  }
});
</script>

<style scoped lang="scss">
.dashboard-page {
  width: 100%; max-width: 1040px; margin: 0 auto;

  .page-header {
    margin-bottom: 24px;
    .page-title { font-size: 24px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; }
    .page-subtitle { font-size: 14px; color: var(--text-secondary); }
  }

  .stats-cards {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 24px;
    .stat-card {
      background-color: var(--surface); border-radius: var(--radius-lg); padding: 20px;
      box-shadow: var(--card-shadow); display: flex; align-items: center; gap: 16px;
      transition: all 0.3s var(--ease-out-expo);
      animation: fade-up 0.5s var(--ease-out-expo) both;
      &:nth-child(1) { animation-delay: 0.05s; }
      &:nth-child(2) { animation-delay: 0.1s; }
      &:nth-child(3) { animation-delay: 0.15s; }
      &:nth-child(4) { animation-delay: 0.2s; }
      &:hover { box-shadow: var(--card-shadow-hover); transform: translateY(-2px); }
      &:active { transform: translateY(0) scale(0.98); box-shadow: var(--card-shadow-active); }
      .stat-icon {
        width: 48px; height: 48px; border-radius: var(--radius-md); display: flex;
        align-items: center; justify-content: center; flex-shrink: 0;
        transition: transform 0.3s var(--ease-spring);
      }
      &:hover .stat-icon { transform: scale(1.05); }
      .stat-info {
        .stat-value { font-size: 24px; font-weight: 700; color: var(--text-primary); line-height: 1.2; }
        .stat-label { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }
      }
    }
  }

  .content-row {
    display: flex; gap: 24px;
    .announcements { width: 320px; flex-shrink: 0; }
    .recent-section { flex: 1; min-width: 0; }
  }

  .section-card {
    background-color: var(--surface); border-radius: var(--radius-lg); padding: 20px; box-shadow: var(--card-shadow);
    animation: fade-up 0.6s var(--ease-out-expo) both;
    .section-header {
      display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;
      .section-title { font-size: 16px; font-weight: 600; color: var(--text-primary); }
    }
  }

  .announcements .section-card { animation-delay: 0.25s; }
  .recent-section .section-card { animation-delay: 0.4s; }

  .announcement-list {
    display: flex; flex-direction: column; gap: 16px;
    .announcement-item {
      display: flex; gap: 12px;
      animation: fade-in 0.6s var(--ease-out-expo) both;
      &:nth-child(1) { animation-delay: 0.3s; }
      &:nth-child(2) { animation-delay: 0.4s; }
      &:nth-child(3) { animation-delay: 0.5s; }

      .announcement-dot {
        width: 8px; height: 8px; border-radius: 50%;
        background: var(--primary-color); margin-top: 6px; flex-shrink: 0;
      }

      .announcement-content {
        flex: 1; min-width: 0;
        .announcement-title {
          font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px;
        }
        .announcement-desc {
          font-size: 12px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 6px;
        }
        .announcement-time {
          font-size: 11px; color: var(--text-secondary);
        }
      }
    }
  }

  .empty-recent {
    display: flex; flex-direction: column; align-items: center; padding: 40px 0;
    p { margin-top: 12px; font-size: 14px; color: var(--text-secondary); }
  }

  .recent-list {
    display: flex; flex-direction: column; gap: 12px;
    .recent-item {
      display: flex; align-items: center; gap: 12px; padding: 12px;
      background-color: var(--bg-muted); border-radius: var(--radius-md); transition: background-color 0.2s ease;
      &:hover { background-color: #f0fdfa; }
      .recent-preview {
        width: 48px; height: 48px; border-radius: var(--radius-sm); overflow: hidden;
        background-color: #e5e7eb; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
        img { width: 100%; height: 100%; object-fit: cover; }
      }
      .recent-info {
        flex: 1; min-width: 0;
        .recent-name { font-size: 14px; font-weight: 500; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .recent-meta { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }
      }
    }
  }
}
</style>
