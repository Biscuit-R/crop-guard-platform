<template>
  <div class="sidebar-container">
    <div class="logo-section">
      <div class="logo-icon">
        <el-icon style="color: white; font-size: 20px"><Monitor /></el-icon>
      </div>
      <div class="logo-text">
        <div class="logo-title">病虫害检测平台</div>
        <div class="logo-subtitle">智能识别 · 精准防护</div>
      </div>
    </div>

    <div class="nav-menu">
      <div
        v-for="item in menuList"
        :key="item.path"
        class="nav-item"
        :class="{ active: currentPath === item.path }"
        @click="handleMenuClick(item)"
      >
        <el-icon :size="18" class="nav-icon"><component :is="item.icon" /></el-icon>
        <span class="nav-text">{{ item.name }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import {
  Monitor,
  DataLine,
  Picture,
  Clock,
  Collection,
  User,
} from "@element-plus/icons-vue";

const router = useRouter();
const route = useRoute();

const menuList = [
  {
    name: "数据看板",
    icon: DataLine,
    path: "/dashboard",
  },
  {
    name: "病虫害检测",
    icon: Picture,
    path: "/detection",
  },
  {
    name: "检测历史",
    icon: Clock,
    path: "/history",
  },
  {
    name: "病虫害图鉴",
    icon: Collection,
    path: "/guide",
  },
  {
    name: "个人中心",
    icon: User,
    path: "/profile",
  },
];

const currentPath = computed(() => route.path);

const handleMenuClick = (item) => {
  router.push(item.path);
};
</script>

<style scoped>
.sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.logo-section {
  height: 72px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid var(--border-color);
}

.logo-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: linear-gradient(135deg, #0d9488 0%, #14b8a6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  flex-shrink: 0;
}

.logo-text {
  overflow: hidden;
}

.logo-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.3;
  white-space: nowrap;
}

.logo-subtitle {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
  line-height: 1.3;
  white-space: nowrap;
}

.nav-menu {
  flex: 1;
  padding: 16px 12px;
}

.nav-item {
  display: flex;
  align-items: center;
  flex-direction: row;
  padding: 14px 12px;
  border-radius: 8px;
  margin-bottom: 4px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
  border-left: 3px solid transparent;
}

.nav-item:hover {
  background-color: var(--primary-light);
}

.nav-item.active {
  background-color: var(--primary-light);
  border-left: 3px solid var(--primary-color);
  color: var(--primary-color);
  font-weight: 500;
}

.nav-item.active .nav-icon {
  color: var(--primary-color);
}

.nav-icon {
  font-size: 18px;
  margin-right: 12px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.nav-text {
  font-size: 14px;
  line-height: 1.4;
}
</style>
