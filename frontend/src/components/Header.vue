<template>
  <div class="header-container">
    <div class="breadcrumbs">
      <el-icon class="breadcrumb-icon"><House /></el-icon>
      <span class="breadcrumb-separator">/</span>
      <span class="breadcrumb-text">{{ currentRouteName }}</span>
    </div>

    <div class="header-actions">
      <div class="action-icons">
        <div class="user-dropdown">
          <el-avatar class="user-avatar" size="32">
            {{ (userStore.userInfo?.username || 'U')[0].toUpperCase() }}
          </el-avatar>
          <div class="user-info">
            <div class="user-name">{{ userStore.userInfo?.username || '用户' }}</div>
            <div class="user-role">普通用户</div>
          </div>
          <el-icon class="dropdown-icon"><CaretBottom /></el-icon>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import {
  CaretBottom,
  House,
} from "@element-plus/icons-vue";
import { useUserStore } from "../stores/user";

const route = useRoute();
const userStore = useUserStore();
const currentRouteName = computed(() => route.meta?.title || "数据看板");

onMounted(async () => {
  if (userStore.isLoggedIn && !userStore.userInfo) {
    try {
      await userStore.fetchUserInfo();
    } catch (error) {
      console.error("获取用户信息失败:", error);
    }
  }
});
</script>

<style scoped>
.header-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.breadcrumbs {
  display: flex;
  align-items: center;
}

.breadcrumb-icon {
  font-size: 14px;
  color: var(--text-secondary);
}

.breadcrumb-separator {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 8px;
}

.breadcrumb-text {
  font-size: 14px;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  align-items: center;
}

.action-icons {
  display: flex;
  align-items: center;
}

.action-icon {
  font-size: 18px;
  color: var(--text-secondary);
  margin-right: 20px;
  cursor: pointer;
  transition: color 0.2s;
}

.action-icon:hover {
  color: var(--primary-color);
}

.user-dropdown {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-md);
  transition: background-color 0.2s ease;
}

.user-dropdown:hover {
  background-color: var(--primary-light);
}

.user-avatar {
  margin-right: 8px;
}

.user-info {
  margin-right: 6px;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.user-role {
  font-size: 12px;
  color: var(--text-secondary);
}

.dropdown-icon {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
