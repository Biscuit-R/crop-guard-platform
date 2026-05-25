<template>
  <div class="profile-page">
    <div class="page-header">
      <h1 class="page-title">个人中心</h1>
      <p class="page-subtitle">管理你的账户信息和使用统计</p>
    </div>

    <div class="profile-content">
      <div class="user-info-card">
        <div class="user-avatar-section">
          <el-avatar class="profile-avatar" size="80">
            {{ (userStore.userInfo?.username || 'U')[0].toUpperCase() }}
          </el-avatar>
          <div class="user-basic-info">
            <div class="user-name">{{ userStore.userInfo?.username || '用户' }}</div>
            <div class="user-email">{{ userStore.userInfo?.email || '' }}</div>
            <div class="user-register-time">
              <el-icon><Calendar /></el-icon>
              注册于 {{ formatDate(userStore.userInfo?.created_at) }}
            </div>
          </div>
        </div>
      </div>

      <div class="stats-cards">
        <div class="stat-card">
          <div class="stat-icon" style="background: #b45309">
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

      <div class="quick-entries">
        <div class="entry-card" @click="$router.push('/history')">
          <div class="entry-icon" style="background: #8b5cf6">
            <el-icon :size="24" color="#ffffff"><Clock /></el-icon>
          </div>
          <div class="entry-info">
            <div class="entry-title">检测历史</div>
            <div class="entry-desc">查看所有检测记录和结果</div>
          </div>
          <el-icon class="entry-arrow"><ArrowRight /></el-icon>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, onMounted } from "vue";
import { Picture, Aim, CircleCheck, Calendar, Clock, ArrowRight } from "@element-plus/icons-vue";
import { useUserStore } from "../stores/user";
import { getDashboardStats } from "../api/dashboard";

const userStore = useUserStore();

const stats = reactive({
  total_detections: 0,
  total_objects: 0,
  success_rate: 0,
  active_days: 0,
});

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

onMounted(async () => {
  if (userStore.isLoggedIn && !userStore.userInfo) {
    try {
      await userStore.fetchUserInfo();
    } catch (e) {
      console.error("获取用户信息失败:", e);
    }
  }

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
});
</script>

<style scoped lang="scss">
.profile-page {
  width: 100%; max-width: 1040px; margin: 0 auto;

  .page-header {
    margin-bottom: 24px;
    .page-title { font-size: 24px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; }
    .page-subtitle { font-size: 14px; color: var(--text-secondary); }
  }

  .profile-content {
    display: flex; flex-direction: column; gap: 24px;
  }

  .user-info-card {
    background-color: var(--surface); border-radius: var(--radius-lg); padding: 24px;
    box-shadow: var(--card-shadow); animation: fade-up 0.5s var(--ease-out-expo) both;

    .user-avatar-section {
      display: flex; align-items: center;

      .profile-avatar {
        background: #b45309; color: #fff; font-size: 32px; font-weight: 600; flex-shrink: 0;
      }

      .user-basic-info {
        margin-left: 24px;

        .user-name { font-size: 24px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
        .user-email { font-size: 14px; color: var(--text-secondary); margin-bottom: 8px; }
        .user-register-time {
          display: flex; align-items: center; gap: 4px;
          font-size: 13px; color: var(--text-secondary);
        }
      }
    }
  }

  .stats-cards {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px;

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

  .quick-entries {
    display: flex; flex-direction: column; gap: 12px;

    .entry-card {
      background-color: var(--surface); border-radius: var(--radius-lg); padding: 20px;
      box-shadow: var(--card-shadow); display: flex; align-items: center; gap: 16px;
      cursor: pointer; transition: all 0.3s var(--ease-out-expo);
      animation: fade-up 0.5s var(--ease-out-expo) both;
      animation-delay: 0.25s;
      &:hover { box-shadow: var(--card-shadow-hover); transform: translateY(-2px); }
      &:active { transform: scale(0.98); }

      .entry-icon {
        width: 48px; height: 48px; border-radius: var(--radius-md); display: flex;
        align-items: center; justify-content: center; flex-shrink: 0;
        transition: transform 0.3s var(--ease-spring);
      }
      &:hover .entry-icon { transform: scale(1.05); }

      .entry-info {
        flex: 1;
        .entry-title { font-size: 16px; font-weight: 600; color: var(--text-primary); }
        .entry-desc { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }
      }
      .entry-arrow { font-size: 18px; color: var(--text-secondary); }
    }
  }
}
</style>
