<template>
  <div class="changelog-page">
    <div class="page-header">
      <el-button class="back-btn" text @click="$router.push('/dashboard')">
        <el-icon><ArrowLeft /></el-icon>
        返回看板
      </el-button>
      <h1 class="page-title">更新日志</h1>
      <p class="page-subtitle">平台版本更新记录与功能变更历史</p>
    </div>

    <div class="timeline">
      <div
        v-for="(entry, idx) in changelog"
        :key="entry.version"
        class="timeline-item"
      >
        <div class="timeline-dot" :class="{ latest: idx === 0 }"></div>
        <div class="timeline-card">
          <div class="card-header">
            <div class="version-info">
              <span class="version-tag" :class="{ latest: idx === 0 }">{{ entry.version }}</span>
              <span class="version-date">{{ entry.date }}</span>
            </div>
          </div>
          <div class="card-body">
            <div v-for="section in entry.sections" :key="section.title" class="change-section">
              <h4 class="section-title">{{ section.title }}</h4>
              <ul class="change-list">
                <li v-for="(item, i) in section.items" :key="i" class="change-item">
                  {{ item }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ArrowLeft } from "@element-plus/icons-vue";

const changelog = [
  {
    version: "v1.2.0",
    date: "2026-05-25",
    sections: [
      {
        title: "新功能",
        items: [
          "讨论区功能上线，支持用户上传图片交流学习，管理员审核管理",
          "更新日志子页面，可查看完整的版本更新历史",
        ],
      },
      {
        title: "模型升级",
        items: [
          "移除 yolo11n 基础模型，仅保留最新训练权重",
          "模型显示名称改为「病虫害检测-v1.0.0-轻量版」格式",
          "默认模型切换为基于 67 类平衡数据集训练的 best.pt",
        ],
      },
      {
        title: "界面优化",
        items: [
          "导航栏精简：检测历史移至个人中心，图鉴移至高级功能",
          "数据看板改为展示当日服务器使用状况",
          "高级功能页卡片排序优化，已上线功能置顶",
        ],
      },
    ],
  },
  {
    version: "v1.1.0",
    date: "2026-05-22",
    sections: [
      {
        title: "UI 动效系统",
        items: [
          "全局统一动效：0.6s fade-up 入场动画、0.3s 悬浮过渡、渐进式显示",
          "所有页面使用 --ease-out-expo / --ease-spring 缓动曲线",
          "卡片悬浮上移、按压缩放、阴影反馈",
          "检测项/列表项逐项递增延迟入场",
        ],
      },
      {
        title: "检测页面重构",
        items: [
          "左侧控制栏：模式切换 + 检测设置 + 模型信息",
          "检测区域：独立圆角矩形卡片（识别清单、AI诊断、操作按钮）",
          "视频检测模式与图片模式统一布局",
          "亚克力背景遮罩效果",
        ],
      },
      {
        title: "登录页面",
        items: [
          "从上到下递进式入场动效（Logo → 表单 → 按钮）",
          "保留原有亚克力卡片设计",
        ],
      },
      {
        title: "数据看板",
        items: [
          "更新公告模块替换快速操作",
          "统计卡片、公告项错开动画延迟",
        ],
      },
      {
        title: "界面统一",
        items: [
          "所有页面 max-width 1040px 居中布局",
          "全局字体提升至 16px",
          "检测面板识别清单窗口缩放适配",
        ],
      },
    ],
  },
  {
    version: "v1.0.0",
    date: "2026-05-20",
    sections: [
      {
        title: "核心功能",
        items: [
          "病虫害检测：单图检测、批量检测、视频检测",
          "视频分析：自动抽帧检测，生成标注视频和统计摘要",
          "检测历史：记录所有检测结果，支持搜索和筛选",
          "病虫害图鉴：102 种常见农作物病虫害资料",
          "数据看板：检测统计和趋势分析",
        ],
      },
      {
        title: "用户系统",
        items: [
          "JWT 认证 + JTI 黑名单机制",
          "admin/user 两级权限管理",
          "记住我功能（localStorage / sessionStorage）",
          "路由守卫 + 管理员权限校验",
        ],
      },
      {
        title: "技术栈",
        items: [
          "后端：Python FastAPI + PostgreSQL + YOLO (ultralytics)",
          "前端：Vue 3 + Vite + Element Plus + Pinia",
          "AI 模型：YOLO11n (102 类农作物病虫害)",
          "基础设施：Docker Compose (PostgreSQL + Redis + MinIO)",
        ],
      },
    ],
  },
];
</script>

<style scoped>
.changelog-page {
  width: 100%;
  max-width: 1040px;
  margin: 0 auto;
  padding-bottom: 24px;
}

.page-header {
  margin-bottom: 32px;
  animation: fade-up 0.6s var(--ease-out-expo) both;
}
.back-btn {
  margin-bottom: 12px;
  padding: 0;
  font-size: 14px;
  color: var(--text-secondary);
  transition: color 0.2s ease;
}
.back-btn:hover {
  color: var(--primary-color);
}
.page-title {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 6px;
  letter-spacing: -0.02em;
}
.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

/* 时间线 */
.timeline {
  position: relative;
  padding-left: 28px;
}
.timeline::before {
  content: '';
  position: absolute;
  left: 7px;
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: var(--border-color);
}

.timeline-item {
  position: relative;
  margin-bottom: 24px;
  animation: fade-up 0.6s var(--ease-out-expo) both;
}
.timeline-item:nth-child(1) { animation-delay: 0.1s; }
.timeline-item:nth-child(2) { animation-delay: 0.2s; }
.timeline-item:nth-child(3) { animation-delay: 0.3s; }
.timeline-item:nth-child(4) { animation-delay: 0.35s; }

.timeline-dot {
  position: absolute;
  left: -24px;
  top: 22px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--border-color);
  border: 2px solid #ffffff;
  z-index: 1;
}
.timeline-dot.latest {
  background: var(--primary-color);
  box-shadow: 0 0 0 4px rgba(180, 83, 9, 0.15);
}

.timeline-card {
  background: #ffffff;
  border-radius: 14px;
  box-shadow: var(--card-shadow);
  border: 1px solid var(--border-color);
  overflow: hidden;
  transition: box-shadow 0.3s var(--ease-out-expo), transform 0.3s var(--ease-out-expo);
}
.timeline-card:hover {
  box-shadow: var(--card-shadow-hover);
  transform: translateY(-2px);
}

.card-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}
.version-info {
  display: flex;
  align-items: center;
  gap: 12px;
}
.version-tag {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  background: #f3f4f6;
  color: var(--text-primary);
}
.version-tag.latest {
  background: var(--primary-color);
  color: #ffffff;
}
.version-date {
  font-size: 13px;
  color: var(--text-secondary);
}

.card-body {
  padding: 16px 20px;
}
.change-section {
  margin-bottom: 16px;
}
.change-section:last-child {
  margin-bottom: 0;
}
.change-section .section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}
.change-list {
  margin: 0;
  padding-left: 18px;
}
.change-item {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.8;
}
</style>
