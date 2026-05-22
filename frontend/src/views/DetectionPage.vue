<template>
  <div class="detection-page">
    <div class="page-header">
      <div class="header-text">
        <h1 class="page-title">上传农作物图片，快速识别病虫害</h1>
        <p class="page-subtitle">支持叶斑病 / 锈病 / 白粉病 / 蚜虫 / 毛虫等多种病虫害检测</p>
      </div>
      <div class="header-controls">
        <div class="control-row">
          <span class="control-label">检测模型</span>
          <el-select v-model="selectedModel" style="width: 200px" @change="handleModelSwitch" :loading="modelsLoading">
            <el-option
              v-for="m in availableModels"
              :key="m.filename"
              :label="`${m.version} (${m.size_mb}MB)`"
              :value="m.filename"
            />
          </el-select>
        </div>
        <div class="control-row">
          <span class="control-label">置信度阈值</span>
          <el-slider v-model="confidence" :min="0.1" :max="1" :step="0.05" :format-tooltip="v => `${(v*100).toFixed(0)}%`" style="width: 160px" />
          <span class="confidence-value">{{ (confidence * 100).toFixed(0) }}%</span>
        </div>
        <div class="control-row">
          <span class="control-label">视频抽帧间隔</span>
          <el-input-number v-model="frameInterval" :min="1" :max="30" size="small" />
          <span class="confidence-value">每{{ frameInterval }}帧</span>
        </div>
      </div>
    </div>

    <FunctionTabs
      ref="functionTabsRef"
      :activeTab="activeTab"
      @tabClick="handleTabClick"
      @fileChange="handleFileChange"
    />

    <!-- 拖拽上传区域 -->
    <div
      class="drop-zone"
      :class="{ 'drag-over': isDragOver }"
      @dragover.prevent="isDragOver = true"
      @dragleave.prevent="isDragOver = false"
      @drop.prevent="handleDrop"
      v-if="!detectionResult && !videoResult"
    >
      <div class="drop-content">
        <el-icon :size="48" class="drop-icon"><UploadFilled /></el-icon>
        <p class="drop-text">拖拽图片到此处上传</p>
        <p class="drop-hint">支持 JPG / PNG / BMP 格式</p>
      </div>
    </div>

    <!-- 批量检测结果切换 -->
    <div v-if="batchResults.length > 1" class="batch-strip">
      <div class="batch-header">
        <span class="batch-title">批量检测结果 ({{ currentIndex + 1 }}/{{ batchResults.length }})</span>
        <div class="batch-nav">
          <el-button size="small" :disabled="currentIndex <= 0" @click="switchBatchImage(currentIndex - 1)">上一张</el-button>
          <el-button size="small" :disabled="currentIndex >= batchResults.length - 1" @click="switchBatchImage(currentIndex + 1)">下一张</el-button>
        </div>
      </div>
      <div class="batch-thumbnails">
        <div
          v-for="(item, idx) in batchResults"
          :key="idx"
          class="batch-thumb"
          :class="{ active: idx === currentIndex, success: item.success, failed: !item.success }"
          @click="switchBatchImage(idx)"
        >
          <img v-if="item.success && item.data" :src="item.data.result_image_url" class="thumb-img" />
          <div v-else class="thumb-error">
            <el-icon><WarningFilled /></el-icon>
          </div>
          <span class="thumb-name">{{ item.filename }}</span>
          <span class="thumb-count" v-if="item.success">{{ item.data?.total_objects || 0 }}个目标</span>
        </div>
      </div>
    </div>

    <!-- 视频检测结果 -->
    <div v-if="videoResult" class="video-result-section">
      <div class="video-player-block">
        <video :src="videoResult.result_video_url" controls class="result-video" />
      </div>
      <div class="video-summary">
        <h3 class="summary-title">检测统计</h3>
        <div class="summary-stats">
          <div class="stat-item">
            <span class="stat-value">{{ videoResult.total_objects }}</span>
            <span class="stat-label">检测目标</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ videoResult.processed_frames }}</span>
            <span class="stat-label">已处理帧</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ videoResult.duration }}s</span>
            <span class="stat-label">视频时长</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ videoResult.detection_time }}s</span>
            <span class="stat-label">检测耗时</span>
          </div>
        </div>
        <div v-if="Object.keys(videoResult.summary).length > 0" class="summary-categories">
          <h4 class="categories-title">病虫害统计</h4>
          <div class="category-list">
            <div v-for="(count, name) in videoResult.summary" :key="name" class="category-item">
              <span class="category-name">{{ name }}</span>
              <span class="category-count">{{ count }} 次</span>
            </div>
          </div>
        </div>
        <div v-if="videoResult.key_frames && videoResult.key_frames.length > 0" class="key-frames">
          <h4 class="categories-title">关键帧截图</h4>
          <div class="key-frame-list">
            <el-image
              v-for="(kf, idx) in videoResult.key_frames"
              :key="idx"
              :src="kf"
              :preview-src-list="videoResult.key_frames"
              :initial-index="idx"
              class="key-frame-img"
            />
          </div>
        </div>
      </div>
    </div>

    <div class="main-content">
      <ImageCompare
        :originalImage="originalImage"
        :resultImage="resultImage"
        :hasResult="!!detectionResult"
      />
      <DetectionPanel
        :modelStatus="modelStatus"
        :detectionResult="detectionResult"
        @redetect="handleRedetect"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { ElMessage, ElLoading } from "element-plus";
import { UploadFilled, WarningFilled } from "@element-plus/icons-vue";
import { detectSingleImage, detectBatchImages, detectVideo, getModels, getModelStatus, switchModel } from "../api/detection";
import FunctionTabs from "../components/FunctionTabs.vue";
import ImageCompare from "../components/ImageCompare.vue";
import DetectionPanel from "../components/DetectionPanel.vue";

const selectedModel = ref("");
const activeTab = ref("single");
const originalImage = ref("");
const resultImage = ref("");
const detectionResult = ref(null);
const isDetecting = ref(false);
const availableModels = ref([]);
const modelsLoading = ref(false);
const modelStatus = ref({});
const functionTabsRef = ref(null);
const confidence = ref(0.5);
const isDragOver = ref(false);

// 批量检测相关
const batchResults = ref([]);
const batchFiles = ref([]);
const currentIndex = ref(0);

// 视频检测相关
const videoResult = ref(null);
const frameInterval = ref(5);

const loadModels = async () => {
  try {
    modelsLoading.value = true;
    const [modelsRes, statusRes] = await Promise.all([getModels(), getModelStatus()]);
    if (modelsRes.success) availableModels.value = modelsRes.data;
    if (statusRes.success) {
      modelStatus.value = statusRes.data;
      const current = modelsRes.data?.find(m => m.is_current);
      if (current) selectedModel.value = current.filename;
    }
  } catch (e) {
    console.error("加载模型列表失败:", e);
  } finally {
    modelsLoading.value = false;
  }
};

const handleModelSwitch = async (filename) => {
  try {
    const loading = ElLoading.service({ text: "切换模型中...", background: "rgba(0,0,0,0.5)" });
    const res = await switchModel(filename);
    loading.close();
    if (res.success) {
      modelStatus.value = res.data;
      availableModels.value.forEach(m => { m.is_current = m.filename === filename; });
      ElMessage.success(`已切换到 ${res.data.model_version}`);
    } else {
      ElMessage.error(res.message || "切换失败");
    }
  } catch (e) {
    console.error("模型切换失败:", e);
    ElMessage.error("模型切换失败");
  }
};

const handleTabClick = (key) => {
  activeTab.value = key;
  const refs = functionTabsRef.value?.fileInputRefs;
  if (refs?.[key]) refs[key].click();
};

const handleFileChange = async (event, tabKey) => {
  event.stopPropagation();
  event.preventDefault();
  const files = event.target.files;
  if (files && files.length > 0) {
    if (tabKey === "single") {
      await performSingleDetection(files[0]);
    } else if (tabKey === "batch") {
      await performBatchDetection(Array.from(files));
    } else if (tabKey === "video") {
      await performVideoDetection(files[0]);
    }
  }
  setTimeout(() => { event.target.value = ''; }, 0);
};

const handleDrop = (e) => {
  isDragOver.value = false;
  const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith("image/"));
  if (files.length === 0) {
    ElMessage.warning("请拖入图片文件");
    return;
  }
  if (files.length === 1) {
    performSingleDetection(files[0]);
  } else {
    performBatchDetection(files);
  }
};

const performSingleDetection = async (file) => {
  const loading = ElLoading.service({ lock: true, text: "正在检测中...", background: "rgba(0, 0, 0, 0.7)" });
  try {
    isDetecting.value = true;
    batchResults.value = [];
    batchFiles.value = [];
    const formData = new FormData();
    formData.append("file", file);
    formData.append("model_name", selectedModel.value);
    formData.append("conf", confidence.value);
    if (originalImage.value) URL.revokeObjectURL(originalImage.value);
    originalImage.value = URL.createObjectURL(file);

    const response = await detectSingleImage(formData);
    if (response.success && response.data) {
      detectionResult.value = response.data;
      resultImage.value = response.data.result_image_url;
      ElMessage.success("检测成功！");
    } else {
      ElMessage.error(response.message || "检测失败");
    }
  } catch (error) {
    console.error("检测错误:", error);
    ElMessage.error("检测失败，请稍后重试");
  } finally {
    isDetecting.value = false;
    loading.close();
  }
};

const performBatchDetection = async (files) => {
  const loading = ElLoading.service({ lock: true, text: `正在批量检测 ${files.length} 张图片...`, background: "rgba(0, 0, 0, 0.7)" });
  try {
    isDetecting.value = true;
    const formData = new FormData();
    files.forEach(f => formData.append("files", f));
    formData.append("model_name", selectedModel.value);
    formData.append("conf", confidence.value);

    if (originalImage.value) URL.revokeObjectURL(originalImage.value);
    originalImage.value = URL.createObjectURL(files[0]);

    const response = await detectBatchImages(formData);
    if (response.success && response.data) {
      batchResults.value = response.data.results;
      batchFiles.value = files;
      currentIndex.value = 0;
      const first = batchResults.value[0];
      if (first?.success && first.data) {
        detectionResult.value = first.data;
        resultImage.value = first.data.result_image_url;
      }
      const successCount = batchResults.value.filter(r => r.success).length;
      ElMessage.success(`批量检测完成：${successCount}/${files.length} 张成功`);
    } else {
      ElMessage.error(response.message || "批量检测失败");
    }
  } catch (error) {
    console.error("批量检测错误:", error);
    ElMessage.error("批量检测失败，请稍后重试");
  } finally {
    isDetecting.value = false;
    loading.close();
  }
};

const performVideoDetection = async (file) => {
  const loading = ElLoading.service({ lock: true, text: "视频检测中，处理时间较长，请耐心等待...", background: "rgba(0, 0, 0, 0.7)" });
  try {
    isDetecting.value = true;
    videoResult.value = null;
    batchResults.value = [];
    detectionResult.value = null;
    const formData = new FormData();
    formData.append("file", file);
    formData.append("model_name", selectedModel.value);
    formData.append("conf", confidence.value);
    formData.append("frame_interval", frameInterval.value);

    const response = await detectVideo(formData);
    if (response.success && response.data) {
      videoResult.value = response.data;
      ElMessage.success("视频检测完成！");
    } else {
      ElMessage.error(response.message || "视频检测失败");
    }
  } catch (error) {
    console.error("视频检测错误:", error);
    ElMessage.error("视频检测失败，请稍后重试");
  } finally {
    isDetecting.value = false;
    loading.close();
  }
};

const switchBatchImage = (idx) => {
  if (idx < 0 || idx >= batchResults.value.length) return;
  currentIndex.value = idx;
  const item = batchResults.value[idx];
  if (item.success && item.data) {
    detectionResult.value = item.data;
    resultImage.value = item.data.result_image_url;
    if (batchFiles.value[idx]) {
      if (originalImage.value) URL.revokeObjectURL(originalImage.value);
      originalImage.value = URL.createObjectURL(batchFiles.value[idx]);
    }
  }
};

const handleRedetect = () => {
  const refs = functionTabsRef.value?.fileInputRefs;
  if (refs?.["single"]) refs["single"].click();
};

onMounted(loadModels);
onUnmounted(() => { if (originalImage.value) URL.revokeObjectURL(originalImage.value); });
</script>

<style scoped>
.detection-page { width: 100%; }

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  gap: 16px;
  flex-wrap: wrap;
}

.header-text { flex: 1; min-width: 200px; }
.page-title { font-size: 28px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; }
.page-subtitle { font-size: 14px; color: var(--text-secondary); }

.header-controls { display: flex; flex-direction: column; gap: 10px; flex-shrink: 0; }
.control-row { display: flex; align-items: center; gap: 8px; }
.control-label { font-size: 13px; color: var(--text-secondary); white-space: nowrap; }
.confidence-value { font-size: 13px; font-weight: 600; color: var(--primary-color); min-width: 36px; }

.drop-zone {
  border: 2px dashed var(--border-color); border-radius: 16px; padding: 48px;
  text-align: center; margin-bottom: 24px; transition: all 0.3s ease;
  background-color: #fafbfc;
}
.drop-zone.drag-over { border-color: var(--primary-color); background-color: var(--primary-light); }
.drop-icon { color: #9ca3af; margin-bottom: 12px; }
.drop-text { font-size: 15px; color: var(--text-primary); margin-bottom: 4px; }
.drop-hint { font-size: 13px; color: var(--text-secondary); }

.batch-strip {
  background-color: #ffffff; border-radius: 12px; padding: 16px; margin-bottom: 24px;
  box-shadow: var(--card-shadow);
}
.batch-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.batch-title { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.batch-nav { display: flex; gap: 8px; }

.batch-thumbnails { display: flex; gap: 12px; overflow-x: auto; padding-bottom: 4px; }
.batch-thumb {
  flex-shrink: 0; width: 100px; border-radius: 8px; overflow: hidden; cursor: pointer;
  border: 2px solid transparent; transition: all 0.2s; background: #f9fafb;
}
.batch-thumb.active { border-color: var(--primary-color); box-shadow: 0 0 0 2px var(--primary-light); }
.batch-thumb.failed { opacity: 0.6; }
.thumb-img { width: 100px; height: 66px; object-fit: cover; display: block; }
.thumb-error { width: 100px; height: 66px; display: flex; align-items: center; justify-content: center; color: #ef4444; }
.thumb-name { display: block; font-size: 11px; padding: 4px 6px 0; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.thumb-count { display: block; font-size: 10px; padding: 2px 6px 4px; color: var(--primary-color); }

.main-content { display: flex; gap: 24px; }

.video-result-section {
  display: flex; gap: 24px; margin-bottom: 24px;
  background: #ffffff; border-radius: 12px; padding: 20px; box-shadow: var(--card-shadow);
}
.video-player-block { flex: 1; min-width: 0; }
.result-video { width: 100%; border-radius: 8px; max-height: 400px; background: #000; }
.video-summary { width: 300px; flex-shrink: 0; }
.summary-title { font-size: 16px; font-weight: 600; color: var(--text-primary); margin-bottom: 16px; }
.summary-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }
.stat-item { display: flex; flex-direction: column; align-items: center; padding: 12px; background: #f9fafb; border-radius: 8px; }
.stat-value { font-size: 20px; font-weight: 700; color: var(--primary-color); }
.stat-label { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }
.categories-title { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 10px; }
.category-list { display: flex; flex-direction: column; gap: 6px; }
.category-item { display: flex; justify-content: space-between; padding: 6px 10px; background: #f9fafb; border-radius: 6px; }
.category-name { font-size: 13px; color: var(--text-primary); }
.category-count { font-size: 13px; font-weight: 500; color: var(--primary-color); }
.key-frame-list { display: flex; gap: 8px; flex-wrap: wrap; }
.key-frame-img { width: 80px; height: 60px; border-radius: 6px; cursor: pointer; }
</style>
