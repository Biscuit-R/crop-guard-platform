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
  DataLine,
  Picture,
  ChatLineSquare,
  Operation,
  User,
  UserFilled,
} from "@element-plus/icons-vue";
import { useUserStore } from "../stores/user";

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

const allMenuItems = computed(() => {
  const items = [
    { name: "数据看板", icon: DataLine, path: "/dashboard" },
    { name: "病虫害检测", icon: Picture, path: "/detection" },
    { name: "讨论区", icon: ChatLineSquare, path: "/discussion" },
    { name: "高级功能", icon: Operation, path: "/tools" },
    { name: "我的", icon: User, path: "/profile" },
  ];
  if (userStore.isAdmin) {
    items.splice(4, 0, { name: "用户管理", icon: UserFilled, path: "/admin" });
  }
  return items;
});

const isActive = (item) => {
  if (item.path === "/tools") return route.path.startsWith("/tools");
  if (item.path === "/admin") return route.path.startsWith("/admin");
  return route.path === item.path;
};

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
