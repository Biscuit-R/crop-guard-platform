<template>
  <div class="right-panel">
    <div class="info-card">
      <div class="info-item">
        <span class="info-label">检测模型</span>
        <span class="info-value">{{ modelStatus.model_version || '-' }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">类别数量</span>
        <span class="info-value">{{ modelStatus.class_count || '-' }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">模型文件</span>
        <span class="info-value" style="font-size:12px;word-break:break-all;">{{ modelStatus.model_path || '-' }}</span>
      </div>
    </div>

    <div class="result-card">
      <div class="card-header">
        <el-icon><List /></el-icon>
        <span class="card-title">识别清单</span>
      </div>
      <div v-if="!detectionResult || detectionResult.total_objects === 0" class="empty-state">
        <el-icon class="empty-icon"><CircleCheck /></el-icon>
        <p class="empty-text">未检测到病虫害</p>
        <p class="empty-desc">请上传农作物图片开始检测</p>
      </div>
      <div v-else class="detection-list">
        <div v-for="(box, index) in detectionResult.boxes" :key="index" class="detection-item">
          <span class="item-name">{{ box.class_name }}</span>
          <span class="item-confidence">{{ (box.confidence * 100).toFixed(1) }}%</span>
        </div>
      </div>
    </div>

    <div class="result-card">
      <div class="card-header">
        <el-icon><ChatDotRound /></el-icon>
        <span class="card-title">AI 诊断建议</span>
      </div>
      <div class="diagnosis-content">
        <p v-if="!detectionResult">上传图片后将自动生成诊断建议</p>
        <p v-else>
          检测到 {{ detectionResult.total_objects }} 个病虫害目标，耗时 {{ detectionResult.detection_time }}s。
          模型: {{ modelStatus.model_version }}
        </p>
      </div>
    </div>

    <div class="action-buttons">
      <el-button size="default" class="btn-secondary" @click="$emit('redetect')">
        <el-icon><Refresh /></el-icon>
        重新检测
      </el-button>
      <el-button type="primary" size="default" class="btn-primary">查看完整报告</el-button>
    </div>
  </div>
</template>

<script setup>
import { List, CircleCheck, ChatDotRound, Refresh } from "@element-plus/icons-vue";

defineProps({
  modelStatus: { type: Object, default: () => ({}) },
  detectionResult: { type: Object, default: null },
});

defineEmits(["redetect"]);
</script>

<style scoped>
.right-panel { width: 360px; display: flex; flex-direction: column; gap: 16px; }

.info-card { background-color: #ffffff; border-radius: 12px; padding: 16px; }
.info-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border-color); }
.info-item:last-child { border-bottom: none; }
.info-label { font-size: 13px; color: var(--text-secondary); }
.info-value { font-size: 13px; font-weight: 500; color: var(--text-primary); }

.result-card { background-color: #ffffff; border-radius: 12px; padding: 16px; }
.card-header { display: flex; align-items: center; margin-bottom: 16px; }
.card-header .el-icon { font-size: 16px; color: var(--primary-color); margin-right: 8px; }
.card-title { font-size: 14px; font-weight: 600; color: var(--text-primary); }

.empty-state { display: flex; flex-direction: column; align-items: center; padding: 32px 0; }
.empty-icon { font-size: 48px; color: var(--success-color); margin-bottom: 12px; }
.empty-text { font-size: 14px; font-weight: 500; color: var(--text-primary); margin-bottom: 4px; }
.empty-desc { font-size: 13px; color: var(--text-secondary); }

.detection-list { display: flex; flex-direction: column; gap: 8px; }
.detection-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background-color: #f9fafb; border-radius: 8px; }
.item-name { font-size: 14px; color: var(--text-primary); }
.item-confidence { font-size: 13px; font-weight: 500; color: var(--primary-color); }

.diagnosis-content { font-size: 13px; color: var(--text-secondary); line-height: 1.6; }

.action-buttons { display: flex; gap: 12px; }
.btn-secondary { flex: 1; border-radius: 8px; padding: 10px; font-size: 14px; }
.btn-primary { flex: 2; border-radius: 8px; padding: 10px; font-size: 14px; background: linear-gradient(135deg, #0d9488, #14b8a6); border-color: #0d9488; }
</style>
