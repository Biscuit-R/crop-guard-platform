<template>
  <div class="sidebar-container">
    <div
      v-for="item in allMenuItems"
      :key="item.path"
      class="nav-item"
      :class="{ active: isActive(item) }"
      @click="handleMenuClick(item)"
    >
      <el-icon :size="20" class="nav-icon"><component :is="item.icon" /></el-icon>
      <span class="nav-text">{{ item.name }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import {
  Picture,
  ChatLineSquare,
  Collection,
  Clock,
  User,
} from "@element-plus/icons-vue";
import { useUserStore } from "../stores/user";

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

// 新版五页：检测 | 历史 | 图鉴 | 问答 | 我的（老版的看板/讨论区/高级功能/用户管理未迁移）
const allMenuItems = computed(() => [
  { name: "检测", icon: Picture, path: "/detection" },
  { name: "历史", icon: Clock, path: "/history" },
  { name: "图鉴", icon: Collection, path: "/guide" },
  { name: "问答", icon: ChatLineSquare, path: "/qa" },
  { name: "我的", icon: User, path: "/profile" },
]);

const isActive = (item) => route.path === item.path;

const handleMenuClick = (item) => {
  router.push(item.path);
};
</script>

<style scoped>
.sidebar-container {
  display: flex;
  align-items: center;
  justify-content: space-around;
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 16px;
  cursor: pointer;
  transition: all 0.25s var(--ease-out-expo);
  border-radius: 10px;
}

.nav-item:hover {
  background-color: var(--primary-light);
  transform: translateY(-1px);
}

.nav-item:active {
  transform: scale(0.95);
}

.nav-item.active {
  color: var(--primary-color);
}

.nav-icon {
  font-size: 20px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.nav-text {
  font-size: 11px;
  color: var(--text-secondary);
}

.nav-item.active .nav-icon {
  color: var(--primary-color);
}

.nav-item.active .nav-text {
  color: var(--primary-color);
  font-weight: 500;
}
</style>
