import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    redirect: "/login",
  },
  {
    path: "/login",
    name: "Login",
    meta: { title: "登录" },
    component: () => import("../views/LoginPage.vue"),
  },
  {
    path: "/register",
    name: "Register",
    meta: { title: "注册" },
    component: () => import("../views/RegisterPage.vue"),
  },
  // 核心功能路由
  {
    path: "/dashboard",
    name: "Dashboard",
    meta: { title: "数据看板" },
    component: () => import("../views/DashboardPage.vue"),
  },
  {
    path: "/detection",
    name: "Detection",
    meta: { title: "病虫害检测" },
    component: () => import("../views/DetectionPage.vue"),
  },
  {
    path: "/history",
    name: "History",
    meta: { title: "检测历史" },
    component: () => import("../views/HistoryPage.vue"),
  },
  {
    path: "/guide",
    name: "PestGuide",
    meta: { title: "病虫害图鉴" },
    component: () => import("../views/PestGuidePage.vue"),
  },
  // 高级功能路由
  {
    path: "/tools",
    name: "Tools",
    meta: { title: "高级功能" },
    component: () => import("../views/AdvancedFeaturesPage.vue"),
  },
  {
    path: "/tools/dataset",
    name: "DatasetConvert",
    meta: { title: "数据集转化" },
    component: () => import("../views/DatasetToolsPage.vue"),
  },
  // 个人中心
  {
    path: "/profile",
    name: "Profile",
    meta: { title: "个人中心" },
    component: () => import("../views/ProfilePage.vue"),
  },
  // 管理员路由
  {
    path: "/admin",
    name: "AdminUsers",
    meta: { title: "用户管理", requiresAdmin: true },
    component: () => import("../views/AdminUsersPage.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("token") || sessionStorage.getItem("token");
  const authPaths = ["/login", "/register"];

  if (authPaths.includes(to.path)) {
    next();
  } else if (!token) {
    next("/login");
  } else {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      if (payload.exp * 1000 < Date.now()) {
        localStorage.removeItem("token");
        sessionStorage.removeItem("token");
        next("/login");
        return;
      }
      if (to.meta.requiresAdmin && payload.role !== "admin") {
        next("/dashboard");
        return;
      }
    } catch {
      localStorage.removeItem("token");
      sessionStorage.removeItem("token");
      next("/login");
      return;
    }
    next();
  }
});

export default router;
