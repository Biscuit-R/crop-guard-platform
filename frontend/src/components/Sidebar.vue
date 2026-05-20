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
      <!-- 核心功能区 -->
      <div class="menu-section">
        <div class="menu-section-title">核心功能</div>
        <div
          v-for="item in mainMenuList"
          :key="item.path"
          class="nav-item"
          :class="{ active: currentPath === item.path }"
          @click="handleMenuClick(item)"
        >
          <el-icon :size="18" class="nav-icon"><component :is="item.icon" /></el-icon>
          <span class="nav-text">{{ item.name }}</span>
        </div>
      </div>

      <!-- 分隔线 -->
      <div class="menu-divider"></div>

      <!-- 高级功能区 -->
      <div class="menu-section">
        <div class="menu-section-title">
          <span>高级功能</span>
          <el-tag size="small" type="warning" effect="plain" class="beta-tag">Beta</el-tag>
        </div>
        <div
          v-for="item in advancedMenuList"
          :key="item.path"
          class="nav-item advanced"
          :class="{ active: isActive(item) }"
          @click="handleMenuClick(item)"
        >
          <el-icon :size="18" class="nav-icon"><component :is="item.icon" /></el-icon>
          <span class="nav-text">{{ item.name }}</span>
          <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
        </div>
      </div>

      <!-- 分隔线 -->
      <div class="menu-divider"></div>

      <!-- 个人中心 -->
      <div class="menu-section">
        <div
          class="nav-item"
          :class="{ active: currentPath === '/profile' }"
          @click="handleMenuClick(profileMenu)"
        >
          <el-icon :size="18" class="nav-icon"><component :is="profileMenu.icon" /></el-icon>
          <span class="nav-text">{{ profileMenu.name }}</span>
        </div>
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
  SetUp,
  Operation,
} from "@element-plus/icons-vue";

const router = useRouter();
const route = useRoute();

// 核心功能菜单
const mainMenuList = [
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
];

// 高级功能菜单
const advancedMenuList = [
  {
    name: "高级功能",
    icon: Operation,
    path: "/tools",
    badge: null,
  },
  // 后续可扩展：
  // {
  //   name: "模型训练",
  //   icon: Cpu,
  //   path: "/tools/training",
  //   badge: "开发中",
  // },
  // {
  //   name: "批量检测",
  //   icon: Files,
  //   path: "/tools/batch",
  //   badge: null,
  // },
];

// 个人中心菜单
const profileMenu = {
  name: "个人中心",
  icon: User,
  path: "/profile",
};

const currentPath = computed(() => route.path);

// 判断菜单项是否激活（支持嵌套路由）
const isActive = (item) => {
  if (item.path === "/tools") {
    return route.path.startsWith("/tools");
  }
  return route.path === item.path;
};

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
  padding: 12px;
  overflow-y: auto;
}

.menu-section {
  margin-bottom: 4px;
}

.menu-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.beta-tag {
  font-size: 10px;
  transform: scale(0.9);
}

.menu-divider {
  height: 1px;
  background: var(--border-color);
  margin: 8px 12px;
}

.nav-item {
  display: flex;
  align-items: center;
  flex-direction: row;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 2px;
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

.nav-item.advanced {
  opacity: 0.85;
}

.nav-item.advanced:hover {
  opacity: 1;
}

.nav-icon {
  font-size: 18px;
  margin-right: 10px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.nav-text {
  font-size: 13px;
  line-height: 1.4;
  flex: 1;
}

.nav-badge {
  font-size: 10px;
  padding: 2px 6px;
  background: #f59e0b;
  color: white;
  border-radius: 10px;
  font-weight: 500;
}
</style>
