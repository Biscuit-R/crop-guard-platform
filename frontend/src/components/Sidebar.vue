<template>
  <div class="sidebar-container" :class="{ 'vertical': isLandscape, 'horizontal': !isLandscape }">
    <template v-if="isLandscape">
      <div class="logo-section">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M7 20h10"/>
            <path d="M12 20v-8"/>
            <path d="M12 12c-3-3-6-2-7 1 3 0 5-1 7-1"/>
            <path d="M12 12c3-3 6-2 7 1-3 0-5-1-7-1"/>
            <path d="M12 8c-2-4-5-4-6-1"/>
            <path d="M12 8c2-4 5-4 6-1"/>
          </svg>
        </div>
        <div class="logo-text">
          <div class="logo-title">病虫害检测平台</div>
        </div>
      </div>
      <div class="nav-menu">
        <div
          v-for="item in allMenuItems"
          :key="item.path"
          class="nav-item"
          :class="{ active: isActive(item) }"
          @click="handleMenuClick(item)"
        >
          <el-icon :size="18" class="nav-icon"><component :is="item.icon" /></el-icon>
          <span class="nav-text">{{ item.name }}</span>
        </div>
      </div>
    </template>

    <template v-else>
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
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import {
  DataLine,
  Picture,
  Clock,
  Collection,
  Operation,
  User,
} from "@element-plus/icons-vue";

const router = useRouter();
const route = useRoute();

const isLandscape = ref(window.innerWidth >= 900 && window.innerWidth > window.innerHeight);

const checkOrientation = () => {
  isLandscape.value = window.innerWidth >= 900 && window.innerWidth > window.innerHeight;
};

onMounted(() => window.addEventListener("resize", checkOrientation));
onUnmounted(() => window.removeEventListener("resize", checkOrientation));

const allMenuItems = [
  { name: "数据看板", icon: DataLine, path: "/dashboard" },
  { name: "病虫害检测", icon: Picture, path: "/detection" },
  { name: "检测历史", icon: Clock, path: "/history" },
  { name: "图鉴", icon: Collection, path: "/guide" },
  { name: "高级功能", icon: Operation, path: "/tools" },
  { name: "我的", icon: User, path: "/profile" },
];

const isActive = (item) => {
  if (item.path === "/tools") return route.path.startsWith("/tools");
  return route.path === item.path;
};

const handleMenuClick = (item) => {
  router.push(item.path);
};
</script>

<style scoped>
.sidebar-container.vertical {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.sidebar-container.horizontal {
  display: flex;
  align-items: center;
  justify-content: space-around;
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
}

/* 竖屏侧栏样式 */
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

.nav-menu {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
}

.vertical .nav-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 2px;
  cursor: pointer;
  transition: all 0.2s;
  border-left: 3px solid transparent;
}

.vertical .nav-item:hover {
  background-color: var(--primary-light);
}

.vertical .nav-item.active {
  background-color: var(--primary-light);
  border-left: 3px solid var(--primary-color);
  color: var(--primary-color);
}

.vertical .nav-icon {
  font-size: 18px;
  margin-right: 10px;
  color: var(--text-secondary);
}

.vertical .nav-text {
  font-size: 13px;
}

/* 横屏底部导航样式 */
.horizontal .nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 16px;
  cursor: pointer;
  transition: all 0.2s;
  border-radius: 8px;
}

.horizontal .nav-item:hover {
  background-color: var(--primary-light);
}

.horizontal .nav-item.active {
  color: var(--primary-color);
}

.horizontal .nav-icon {
  font-size: 20px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.horizontal .nav-text {
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
