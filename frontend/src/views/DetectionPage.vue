<template>
  <div class="detection-page">
    <!-- 页头：标题 + 副标题 -->
    <div class="page-header">
      <h1 class="page-title">病虫害检测</h1>
      <p class="page-subtitle">上传农作物图片或视频，AI 自动识别病虫害</p>
    </div>

    <!-- 主体：左侧控制栏 + 右侧检测区 -->
    <div class="main-body">
      <!-- 控制栏：模式切换 + 设置 -->
      <aside class="controls-sidebar">
        <div class="mode-switch">
          <button
            v-for="m in modes"
            :key="m.key"
            class="mode-btn"
            :class="{ active: activeMode === m.key }"
            @click="activeMode = m.key"
          >
            <el-icon :size="16"><component :is="m.icon" /></el-icon>
            <span>{{ m.label }}</span>
          </button>
        </div>
        <div class="settings-inline">
          <div class="settings-title">
            <el-icon><Setting /></el-icon>
            <span>检测设置</span>
          </div>
          <div class="settings-row">
            <span class="settings-label">检测模型</span>
            <el-select v-model="selectedModel" size="small" style="width: 100%" @change="handleModelSwitch" :loading="modelsLoading">
              <el-option v-for="m in availableModels" :key="m.filename" :label="`${m.version} (${m.size_mb}MB)`" :value="m.filename" />
            </el-select>
          </div>
          <div class="settings-row">
            <span class="settings-label">置信度阈值</span>
            <el-slider v-model="confidence" :min="0.1" :max="1" :step="0.05" :format-tooltip="v => `${(v*100).toFixed(0)}%`" />
            <span class="slider-value">{{ (confidence * 100).toFixed(0) }}%</span>
          </div>
          <div class="settings-row" v-if="activeMode === 'video'">
            <span class="settings-label">抽帧间隔</span>
            <el-input-number v-model="frameInterval" :min="1" :max="30" size="small" style="width: 100%" />
          </div>
        </div>
        <!-- 模型信息 -->
        <div class="model-info-card">
          <div class="model-info-item">
            <span class="model-info-label">检测模型</span>
            <span class="model-info-value">{{ modelStatus.model_version || '-' }}</span>
          </div>
          <div class="model-info-item">
            <span class="model-info-label">类别数量</span>
            <span class="model-info-value">{{ modelStatus.class_count || '-' }}</span>
          </div>
          <div class="model-info-item">
            <span class="model-info-label">模型文件</span>
            <span class="model-info-value model-path">{{ modelStatus.model_path || '-' }}</span>
          </div>
        </div>
      </aside>

      <!-- 检测内容区 -->
      <div class="content-area">
        <!-- 图片检测模式 -->
        <template v-if="activeMode === 'image'">
          <div class="result-layout">
            <div class="result-left" :class="{ 'has-result': detectionResult || videoResult }">
              <!-- 无结果：上传区域 -->
              <div v-if="!detectionResult" class="upload-section">
                <div
                  class="upload-area"
                  :class="{ 'drag-over': isDragOver }"
                  @dragover.prevent="isDragOver = true"
                  @dragleave.prevent="isDragOver = false"
                  @drop.prevent="handleDrop"
                >
                  <div class="upload-prompt">
                    <div class="upload-icon-wrap">
                      <el-icon :size="32"><UploadFilled /></el-icon>
                    </div>
                    <div class="upload-text">
                      <p class="upload-main">拖拽图片到此处，或点击上传</p>
                      <p class="upload-hint">支持 JPG / PNG / BMP，可多选批量检测</p>
                    </div>
                    <div class="upload-actions">
                      <el-button type="primary" @click="triggerUpload('single')">
                        <el-icon><Picture /></el-icon>单图检测
                      </el-button>
                      <el-button @click="triggerUpload('batch')">
                        <el-icon><Plus /></el-icon>批量检测
                      </el-button>
                    </div>
                    <input ref="singleInputRef" type="file" accept="image/*" class="hidden-input" @change="e => handleFileChange(e, 'single')" />
                    <input ref="batchInputRef" type="file" accept="image/*" multiple class="hidden-input" @change="e => handleFileChange(e, 'batch')" />
                  </div>
                </div>
              </div>

              <!-- 有结果：图片对比 -->
              <template v-else>
                <div class="result-header">
                  <span class="result-title">检测结果</span>
                  <el-button size="small" text @click="resetDetection">
                    <el-icon><RefreshLeft /></el-icon>重新检测
                  </el-button>
                </div>
                <ImageCompare
                  :originalImage="originalImage"
                  :resultImage="resultImage"
                  :hasResult="!!detectionResult"
                />
                <!-- 批量缩略图条 -->
                <div v-if="batchResults.length > 1" class="batch-strip">
                  <div class="batch-header">
                    <span class="batch-info">{{ currentIndex + 1 }} / {{ batchResults.length }} 张</span>
                    <div class="batch-nav">
                      <el-button size="small" :icon="ArrowLeft" :disabled="currentIndex <= 0" @click="switchBatchImage(currentIndex - 1)" circle />
                      <el-button size="small" :icon="ArrowRight" :disabled="currentIndex >= batchResults.length - 1" @click="switchBatchImage(currentIndex + 1)" circle />
                    </div>
                  </div>
                  <div class="batch-thumbnails">
                    <div
                      v-for="(item, idx) in batchResults"
                      :key="idx"
                      class="batch-thumb"
                      :class="{ active: idx === currentIndex, failed: !item.success }"
                      @click="switchBatchImage(idx)"
                    >
                      <img v-if="item.success && item.data" :src="item.data.result_image_url" class="thumb-img" />
                      <div v-else class="thumb-error"><el-icon><WarningFilled /></el-icon></div>
                      <span class="thumb-count" v-if="item.success">{{ item.data?.total_objects || 0 }}</span>
                    </div>
                  </div>
                </div>
              </template>
            </div>
            <DetectionPanel
              :modelStatus="modelStatus"
              :detectionResult="detectionResult"
              @redetect="resetDetection"
            />
          </div>
        </template>

        <!-- 视频检测模式 -->
        <template v-if="activeMode === 'video'">
          <div class="result-layout">
            <div class="result-left" :class="{ 'has-result': detectionResult || videoResult }">
              <!-- 无结果：上传区域 -->
              <div v-if="!videoResult" class="upload-section">
                <div
                  class="upload-area"
                  :class="{ 'drag-over': isDragOver }"
                  @dragover.prevent="isDragOver = true"
                  @dragleave.prevent="isDragOver = false"
                  @drop.prevent="handleVideoDrop"
                >
                  <div class="upload-prompt">
                    <div class="upload-icon-wrap video">
                      <el-icon :size="32"><VideoCamera /></el-icon>
                    </div>
                    <div class="upload-text">
                      <p class="upload-main">拖拽视频到此处，或点击上传</p>
                      <p class="upload-hint">支持 MP4 / AVI / MOV，最大 200MB</p>
                    </div>
                    <div class="upload-actions">
                      <el-button type="primary" @click="triggerUpload('video')">
                        <el-icon><VideoCamera /></el-icon>选择视频
                      </el-button>
                    </div>
                    <input ref="videoInputRef" type="file" accept="video/*" class="hidden-input" @change="e => handleFileChange(e, 'video')" />
                  </div>
                </div>
              </div>

              <!-- 有结果：视频播放 + 统计 -->
              <template v-else>
                <div class="result-header">
                  <span class="result-title">视频检测结果</span>
                  <el-button size="small" text @click="videoResult = null">
                    <el-icon><RefreshLeft /></el-icon>重新检测
                  </el-button>
                </div>
                <video :src="videoResult.result_video_url" controls class="result-video" />
                <div class="video-summary">
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
                    <div class="cat-title">病虫害统计</div>
                    <div v-for="(count, name) in videoResult.summary" :key="name" class="cat-item">
                      <span class="cat-name">{{ name }}</span>
                      <span class="cat-count">{{ count }}</span>
                    </div>
                  </div>
                  <div v-if="videoResult.key_frames?.length > 0" class="key-frames">
                    <div class="cat-title">关键帧</div>
                    <div class="kf-list">
                      <el-image
                        v-for="(kf, idx) in videoResult.key_frames"
                        :key="idx"
                        :src="kf"
                        :preview-src-list="videoResult.key_frames"
                        :initial-index="idx"
                        class="kf-img"
                      />
                    </div>
                  </div>
                </div>
              </template>
            </div>
            <DetectionPanel
              :modelStatus="modelStatus"
              :detectionResult="videoPanelResult"
              @redetect="videoResult = null"
            />
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { ElMessage, ElLoading } from "element-plus";
import {
  UploadFilled, Picture, Plus, VideoCamera, Setting,
  RefreshLeft, ArrowLeft, ArrowRight, WarningFilled,
} from "@element-plus/icons-vue";
import { detectSingleImage, detectBatchImages, detectVideo, getModels, getModelStatus, switchModel } from "../api/detection";
import ImageCompare from "../components/ImageCompare.vue";
import DetectionPanel from "../components/DetectionPanel.vue";

const modes = [
  { key: "image", label: "图片检测", icon: Picture },
  { key: "video", label: "视频检测", icon: VideoCamera },
];

const activeMode = ref("image");
const selectedModel = ref("");
const confidence = ref(0.5);
const frameInterval = ref(5);
const isDetecting = ref(false);
const isDragOver = ref(false);

const availableModels = ref([]);
const modelsLoading = ref(false);
const modelStatus = ref({});

const originalImage = ref("");
const resultImage = ref("");
const detectionResult = ref(null);
const batchResults = ref([]);
const batchFiles = ref([]);
const currentIndex = ref(0);
const videoResult = ref(null);

const videoPanelResult = computed(() => {
  if (!videoResult.value) return null;
  const v = videoResult.value;
  const boxes = Object.entries(v.summary || {}).map(([class_name, count]) => ({
    class_name: `${class_name} (${count}次)`,
    confidence: 1,
  }));
  return {
    total_objects: v.total_objects,
    detection_time: v.detection_time,
    boxes,
  };
});

const singleInputRef = ref(null);
const batchInputRef = ref(null);
const videoInputRef = ref(null);

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
    }
  } catch {
    ElMessage.error("模型切换失败");
  }
};

const triggerUpload = (type) => {
  if (type === "single") singleInputRef.value?.click();
  else if (type === "batch") batchInputRef.value?.click();
  else if (type === "video") videoInputRef.value?.click();
};

const handleFileChange = async (event, type) => {
  event.stopPropagation();
  event.preventDefault();
  const files = event.target.files;
  if (!files?.length) return;
  if (type === "single") await performSingleDetection(files[0]);
  else if (type === "batch") await performBatchDetection(Array.from(files));
  else if (type === "video") await performVideoDetection(files[0]);
  setTimeout(() => { event.target.value = ""; }, 0);
};

const handleDrop = (e) => {
  isDragOver.value = false;
  const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith("image/"));
  if (!files.length) { ElMessage.warning("请拖入图片文件"); return; }
  files.length === 1 ? performSingleDetection(files[0]) : performBatchDetection(files);
};

const handleVideoDrop = (e) => {
  isDragOver.value = false;
  const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith("video/"));
  if (!files.length) { ElMessage.warning("请拖入视频文件"); return; }
  performVideoDetection(files[0]);
};

const resetDetection = () => {
  detectionResult.value = null;
  resultImage.value = "";
  batchResults.value = [];
  batchFiles.value = [];
  currentIndex.value = 0;
  if (originalImage.value) URL.revokeObjectURL(originalImage.value);
  originalImage.value = "";
};

const performSingleDetection = async (file) => {
  const loading = ElLoading.service({ lock: true, text: "正在检测中...", background: "rgba(0,0,0,0.7)" });
  try {
    isDetecting.value = true;
    resetDetection();
    const formData = new FormData();
    formData.append("file", file);
    formData.append("model_name", selectedModel.value);
    formData.append("conf", confidence.value);
    originalImage.value = URL.createObjectURL(file);
    const res = await detectSingleImage(formData);
    if (res.success && res.data) {
      detectionResult.value = res.data;
      resultImage.value = res.data.result_image_url;
      ElMessage.success("检测成功");
    } else {
      ElMessage.error(res.message || "检测失败");
    }
  } catch {
    ElMessage.error("检测失败，请稍后重试");
  } finally {
    isDetecting.value = false;
    loading.close();
  }
};

const performBatchDetection = async (files) => {
  const loading = ElLoading.service({ lock: true, text: `批量检测 ${files.length} 张图片...`, background: "rgba(0,0,0,0.7)" });
  try {
    isDetecting.value = true;
    const formData = new FormData();
    files.forEach(f => formData.append("files", f));
    formData.append("model_name", selectedModel.value);
    formData.append("conf", confidence.value);
    originalImage.value = URL.createObjectURL(files[0]);
    const res = await detectBatchImages(formData);
    if (res.success && res.data) {
      batchResults.value = res.data.results;
      batchFiles.value = files;
      currentIndex.value = 0;
      const first = batchResults.value[0];
      if (first?.success && first.data) {
        detectionResult.value = first.data;
        resultImage.value = first.data.result_image_url;
      }
      ElMessage.success(`批量检测完成：${batchResults.value.filter(r => r.success).length}/${files.length} 张`);
    }
  } catch {
    ElMessage.error("批量检测失败");
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

const performVideoDetection = async (file) => {
  const loading = ElLoading.service({ lock: true, text: "视频检测中，请耐心等待...", background: "rgba(0,0,0,0.7)" });
  try {
    isDetecting.value = true;
    videoResult.value = null;
    const formData = new FormData();
    formData.append("file", file);
    formData.append("model_name", selectedModel.value);
    formData.append("conf", confidence.value);
    formData.append("frame_interval", frameInterval.value);
    const res = await detectVideo(formData);
    if (res.success && res.data) {
      videoResult.value = res.data;
      ElMessage.success("视频检测完成");
    }
  } catch {
    ElMessage.error("视频检测失败");
  } finally {
    isDetecting.value = false;
    loading.close();
  }
};

onMounted(loadModels);
onUnmounted(() => { if (originalImage.value) URL.revokeObjectURL(originalImage.value); });
</script>

<style scoped>
.detection-page { width: 100%; max-width: 1040px; margin: 0 auto; }

/* === 页头 === */
.page-header { margin-bottom: 24px; }
.page-title { font-size: 26px; font-weight: 700; color: var(--text-primary); margin-bottom: 6px; letter-spacing: -0.02em; }
.page-subtitle { font-size: 14px; color: var(--text-secondary); margin: 0; }

/* === 主体布局 === */
.main-body {
  display: flex;
  gap: 16px;
}

.controls-sidebar {
  width: 200px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.content-area {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.result-layout {
  display: flex; flex-direction: column; gap: 16px;
}

.result-left {
  flex: 2; min-width: 0;
  background: #ffffff; border-radius: 14px; padding: 24px;
  display: flex; flex-direction: column;
}
.result-left.has-result {
  align-self: flex-start;
}

/* === 模式切换 === */
.mode-switch {
  display: flex;
  flex-direction: column;
  background: #f1f5f9;
  border-radius: 12px;
  padding: 4px;
  gap: 2px;
}
.mode-btn {
  display: flex; align-items: center; gap: 8px; padding: 12px 14px;
  border: none; background: transparent; border-radius: 10px; cursor: pointer;
  font-size: 14px; font-weight: 500; color: var(--text-secondary);
  transition: all 0.2s ease; width: 100%;
}
.mode-btn:hover { color: var(--text-primary); background: rgba(255,255,255,0.5); }
.mode-btn.active {
  color: var(--primary-color); background: #ffffff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

/* === 设置面板（内联） === */
.settings-inline {
  background: #ffffff; border-radius: 14px; padding: 18px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.settings-title {
  display: flex; align-items: center; gap: 6px;
  font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 16px;
  .el-icon { font-size: 15px; color: var(--primary-color); }
}
.settings-row { margin-bottom: 12px; }
.settings-row:last-child { margin-bottom: 0; }
.settings-label { display: block; font-size: 12px; color: var(--text-secondary); margin-bottom: 6px; }
.slider-value { font-size: 13px; font-weight: 600; color: var(--primary-color); text-align: center; margin-top: 2px; display: block; }

/* === 模型信息卡片 === */
.model-info-card {
  background: #ffffff; border-radius: 12px; padding: 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.model-info-item {
  display: flex; justify-content: space-between; align-items: flex-start;
  padding: 8px 0; border-bottom: 1px solid #f3f4f6;
}
.model-info-item:last-child { border-bottom: none; }
.model-info-label { font-size: 12px; color: var(--text-secondary); flex-shrink: 0; }
.model-info-value { font-size: 12px; font-weight: 500; color: var(--text-primary); text-align: right; margin-left: 8px; }
.model-info-value.model-path { font-size: 11px; word-break: break-all; }

/* === 上传区域 === */
.upload-section { flex: 1; display: flex; }
.upload-area {
  border: 2px dashed #d1d5db; border-radius: 18px; transition: all 0.25s ease;
  background: #fafbfc; overflow: hidden;
  min-height: 280px;
  flex: 1;
  display: flex; align-items: center; justify-content: center;
}
.upload-area.drag-over { border-color: var(--primary-color); background: var(--primary-light); }

.upload-prompt {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 48px 24px; gap: 20px;
}
.upload-icon-wrap {
  width: 72px; height: 72px; border-radius: 18px; background: #f1f5f9;
  display: flex; align-items: center; justify-content: center; color: #94a3b8;
}
.upload-icon-wrap.video { background: #eff6ff; color: #3b82f6; }
.upload-text { text-align: center; }
.upload-main { font-size: 16px; color: var(--text-primary); margin-bottom: 6px; }
.upload-hint { font-size: 13px; color: var(--text-secondary); }
.upload-actions { display: flex; gap: 12px; margin-top: 8px; }
.hidden-input { display: none; }

/* === 结果区域 === */
.result-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.result-title { font-size: 15px; font-weight: 600; color: var(--text-primary); }

/* === 批量缩略图 === */
.batch-strip { margin-top: 16px; }
.batch-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.batch-info { font-size: 13px; font-weight: 500; color: var(--text-secondary); }
.batch-nav { display: flex; gap: 6px; }
.batch-thumbnails { display: flex; gap: 10px; overflow-x: auto; padding-bottom: 4px; }
.batch-thumb {
  flex-shrink: 0; width: 72px; height: 52px; border-radius: 8px; overflow: hidden;
  cursor: pointer; border: 2px solid transparent; transition: all 0.2s; position: relative;
  background: #f1f5f9;
}
.batch-thumb.active { border-color: var(--primary-color); box-shadow: 0 0 0 2px rgba(13,148,136,0.15); }
.batch-thumb.failed { opacity: 0.5; }
.thumb-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.thumb-error { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: #ef4444; }
.thumb-count {
  position: absolute; bottom: 2px; right: 2px; font-size: 10px; font-weight: 600;
  background: rgba(13,148,136,0.9); color: #fff; padding: 1px 5px; border-radius: 4px;
}

/* === 视频结果 === */
.result-video { width: 100%; border-radius: 10px; background: #000; margin-bottom: 16px; }
.summary-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 18px; }
.stat-item { display: flex; flex-direction: column; align-items: center; padding: 12px 8px; background: #f9fafb; border-radius: 10px; }
.stat-value { font-size: 18px; font-weight: 700; color: var(--primary-color); }
.stat-label { font-size: 11px; color: var(--text-secondary); margin-top: 2px; }
.cat-title { font-size: 13px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; }
.cat-item { display: flex; justify-content: space-between; padding: 5px 10px; background: #f9fafb; border-radius: 6px; margin-bottom: 4px; }
.cat-name { font-size: 13px; color: var(--text-primary); }
.cat-count { font-size: 13px; font-weight: 600; color: var(--primary-color); }
.key-frames { margin-top: 14px; }
.kf-list { display: flex; gap: 6px; flex-wrap: wrap; }
.kf-img { width: 72px; height: 52px; border-radius: 6px; cursor: pointer; }
</style>
