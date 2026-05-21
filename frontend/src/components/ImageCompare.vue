<template>
  <div class="left-panel">
    <div class="panel-header">
      <span class="panel-title">检测预览</span>
      <el-tag v-if="hasResult" type="success" effect="light" class="result-tag">
        <el-icon class="el-icon--left"><Check /></el-icon>
        检测完成
      </el-tag>
      <el-tag v-else type="info" effect="light" class="result-tag">等待上传</el-tag>
    </div>

    <div class="toolbar">
      <el-button :class="{ active: compareMode === 'side' }" size="small" @click="$emit('update:compareMode', 'side')">
        <el-icon><Minus /></el-icon>
        并排对比
      </el-button>
      <el-button :class="{ active: compareMode === 'grid' }" size="small" @click="$emit('update:compareMode', 'grid')">
        <el-icon><Grid /></el-icon>
        栅格对比
      </el-button>
    </div>

    <div class="image-compare">
      <div class="image-card">
        <img v-if="originalImage" :src="originalImage" alt="原始图片" class="compare-image" />
        <div v-else class="image-placeholder">
          <el-icon :size="48" color="#d1d5db"><Picture /></el-icon>
          <p>原始图片</p>
        </div>
        <div class="image-label">原始图片</div>
      </div>
      <div class="image-card">
        <img v-if="resultImage" :src="resultImage" alt="检测结果" class="compare-image" />
        <div v-else class="image-placeholder">
          <el-icon :size="48" color="#d1d5db"><Picture /></el-icon>
          <p>检测结果</p>
        </div>
        <div class="image-label">检测结果</div>
        <div class="detection-mark" v-if="hasResult"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Picture, Check, Grid, Minus } from "@element-plus/icons-vue";

defineProps({
  originalImage: { type: String, default: "" },
  resultImage: { type: String, default: "" },
  hasResult: { type: Boolean, default: false },
  compareMode: { type: String, default: "side" },
});

defineEmits(["update:compareMode"]);
</script>

<style scoped>
.left-panel {
  flex: 1; background-color: #ffffff; border-radius: 12px; padding: 20px;
}
.panel-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;
}
.panel-title { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.result-tag { padding: 4px 12px; border-radius: 20px; font-size: 13px; }

.toolbar { display: flex; gap: 8px; margin-bottom: 16px; }
.toolbar .el-button { border-radius: 6px; padding: 6px 14px; }
.toolbar .el-button.active {
  background-color: var(--primary-light); color: var(--primary-color); border-color: var(--primary-color);
}

.image-compare { display: flex; gap: 16px; height: 320px; }
.image-card {
  flex: 1; position: relative; border-radius: 8px; overflow: hidden; background-color: #f9fafb;
}
.compare-image { width: 100%; height: 100%; object-fit: contain; }
.image-placeholder {
  width: 100%; height: 100%; display: flex; flex-direction: column;
  align-items: center; justify-content: center; color: var(--text-secondary);
}
.image-placeholder p { margin-top: 8px; font-size: 13px; }
.image-label {
  position: absolute; bottom: 0; left: 0; right: 0;
  padding: 8px 12px; background: rgba(0, 0, 0, 0.5); color: #ffffff; font-size: 13px;
}
.detection-mark {
  position: absolute; top: 12px; right: 12px; width: 36px; height: 36px;
  border-radius: 50%; background-color: var(--primary-color);
  display: flex; align-items: center; justify-content: center;
}
.detection-mark::after { content: "\2713"; color: #ffffff; font-size: 18px; font-weight: bold; }
</style>
