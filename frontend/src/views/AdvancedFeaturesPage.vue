<template>
  <div class="advanced-features-page">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">高级功能</h1>
        <p class="page-desc">面向开发者和研究人员的专业工具</p>
      </div>
      <el-tag type="warning" effect="dark" size="large">Beta</el-tag>
    </div>

    <!-- 功能卡片网格 -->
    <div class="features-grid">
      <!-- 数据集转化 -->
      <el-card class="feature-card" shadow="hover" @click="navigateTo('/tools/dataset')">
        <div class="feature-icon dataset">
          <el-icon :size="32"><SetUp /></el-icon>
        </div>
        <h3 class="feature-title">数据集转化</h3>
        <p class="feature-desc">将 VOC、COCO、CSV 格式的数据集自动转化为 YOLO 训练格式</p>
        <div class="feature-tags">
          <el-tag size="small" type="success">已上线</el-tag>
          <el-tag size="small" type="info">VOC</el-tag>
          <el-tag size="small" type="info">COCO</el-tag>
          <el-tag size="small" type="info">CSV</el-tag>
        </div>
      </el-card>

      <!-- 模型训练（开发中） -->
      <el-card class="feature-card disabled" shadow="hover">
        <div class="feature-icon training">
          <el-icon :size="32"><Cpu /></el-icon>
        </div>
        <h3 class="feature-title">模型训练</h3>
        <p class="feature-desc">在线配置训练参数，上传数据集进行模型微调训练</p>
        <div class="feature-tags">
          <el-tag size="small" type="warning">开发中</el-tag>
        </div>
      </el-card>

      <!-- 批量检测（开发中） -->
      <el-card class="feature-card disabled" shadow="hover">
        <div class="feature-icon batch">
          <el-icon :size="32"><Files /></el-icon>
        </div>
        <h3 class="feature-title">批量检测</h3>
        <p class="feature-desc">一次性上传多张图片，批量进行病虫害检测并导出报告</p>
        <div class="feature-tags">
          <el-tag size="small" type="warning">开发中</el-tag>
        </div>
      </el-card>

      <!-- 模型导出（计划中） -->
      <el-card class="feature-card disabled" shadow="hover">
        <div class="feature-icon export">
          <el-icon :size="32"><Download /></el-icon>
        </div>
        <h3 class="feature-title">模型导出</h3>
        <p class="feature-desc">将训练好的模型导出为 ONNX、TensorRT 等格式，支持边缘设备部署</p>
        <div class="feature-tags">
          <el-tag size="small" type="info">计划中</el-tag>
        </div>
      </el-card>

      <!-- API 接口（计划中） -->
      <el-card class="feature-card disabled" shadow="hover">
        <div class="feature-icon api">
          <el-icon :size="32"><Connection /></el-icon>
        </div>
        <h3 class="feature-title">API 接口</h3>
        <p class="feature-desc">开放 RESTful API，支持第三方系统集成和自动化检测</p>
        <div class="feature-tags">
          <el-tag size="small" type="info">计划中</el-tag>
        </div>
      </el-card>

      <!-- 插件系统（计划中） -->
      <el-card class="feature-card disabled" shadow="hover">
        <div class="feature-icon plugin">
          <el-icon :size="32"><Grid /></el-icon>
        </div>
        <h3 class="feature-title">插件系统</h3>
        <p class="feature-desc">支持自定义检测规则、报告模板、告警通知等插件扩展</p>
        <div class="feature-tags">
          <el-tag size="small" type="info">计划中</el-tag>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router";
import {
  SetUp,
  Cpu,
  Files,
  Download,
  Connection,
  Grid,
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";

const router = useRouter();

const navigateTo = (path) => {
  router.push(path);
};
</script>

<style scoped>
.advanced-features-page {
  max-width: 1040px; margin: 0 auto; padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.page-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.feature-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.feature-card:hover {
  border-color: var(--primary-color);
  transform: translateY(-4px);
}

.feature-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.feature-card.disabled:hover {
  border-color: var(--border-color);
  transform: none;
}

.feature-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  color: white;
}

.feature-icon.dataset {
  background: #0d9488;
}

.feature-icon.training {
  background: #3b82f6;
}

.feature-icon.batch {
  background: #8b5cf6;
}

.feature-icon.export {
  background: #f59e0b;
}

.feature-icon.api {
  background: #ec4899;
}

.feature-icon.plugin {
  background: #6366f1;
}

.feature-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.feature-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 16px 0;
  min-height: 42px;
}

.feature-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
</style>
