import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    redirect: "/login",
  },
  {
    path: "/login",
    name: "登录",
    component: () => import("../views/LoginPage.vue"),
  },
  {
    path: "/register",
    name: "注册",
    component: () => import("../views/RegisterPage.vue"),
  },
  {
    path: "/dashboard",
    name: "数据看板",
    component: () => import("../views/DashboardPage.vue"),
  },
  {
    path: "/detection",
    name: "病虫害检测",
    component: () => import("../views/DetectionPage.vue"),
  },
  {
    path: "/history",
    name: "检测历史",
    component: () => import("../views/HistoryPage.vue"),
  },
  {
    path: "/guide",
    name: "病虫害图鉴",
    component: () => import("../views/PestGuidePage.vue"),
  },
  {
    path: "/profile",
    name: "个人中心",
    component: () => import("../views/ProfilePage.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("token");
  const authPaths = ["/login", "/register"];

  if (authPaths.includes(to.path)) {
    next();
  } else if (!token) {
    next("/login");
  } else {
    next();
  }
});

export default router;
