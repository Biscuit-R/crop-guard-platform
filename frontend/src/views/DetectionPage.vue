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
              <el-option v-for="m in availableModels" :key="m.filename" :label="m.display_name || m.filename" :value="m.filename">
                <span>{{ m.display_name || m.filename }}</span>
                <span v-if="m.description" class="model-option-desc">{{ m.description }}</span>
              </el-option>
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
        <!-- 文件输入（始终渲染，确保 ref 始终有效） -->
        <input ref="singleInputRef" type="file" accept="image/*" class="hidden-input" @change="e => handleFileChange(e, 'single')" />
        <input ref="batchInputRef" type="file" accept="image/*" multiple class="hidden-input" @change="e => handleFileChange(e, 'batch')" />
        <input ref="videoInputRef" type="file" accept="video/*" class="hidden-input" @change="e => handleFileChange(e, 'video')" />

        <!-- 图片检测模式 -->
        <template v-if="activeMode === 'image'">
          <div class="result-layout">
            <div class="result-left">
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
                  </div>
                </div>
              </div>

              <!-- 有结果：图片对比 -->
              <template v-else>
                <div class="result-header">
                  <span class="result-title">检测结果</span>
                  <el-button size="small" text @click="triggerUpload('single')">
                    <el-icon><RefreshLeft /></el-icon>更换图片
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
              :selectedName="popoverSelectedName"
              mode="image"
              @redetect="handleRedetect"
              @generate-report="handleGenerateReport"
              @select-pest="handleSelectPest"
            />
          </div>
        </template>

        <!-- 视频检测模式 -->
        <template v-if="activeMode === 'video'">
          <div class="result-layout">
            <div class="result-left">
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
                  </div>
                </div>
              </div>

              <!-- 有结果：视频播放 + 统计 -->
              <template v-else>
                <div class="result-header">
                  <span class="result-title">视频检测结果</span>
                  <el-button size="small" text @click="triggerUpload('video')">
                    <el-icon><RefreshLeft /></el-icon>更换视频
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
              :selectedName="popoverSelectedName"
              mode="video"
              @redetect="handleRedetect"
              @generate-report="handleGenerateReport"
              @select-pest="handleSelectPest"
            />
          </div>
        </template>

        <!-- 实时摄像头检测模式 -->
        <template v-if="activeMode === 'camera'">
          <div class="result-layout">
            <div class="result-left">
              <div class="camera-view">
                <div class="camera-container">
                  <video ref="cameraVideoRef" class="camera-video" :class="{ hidden: !cameraActive }" autoplay playsinline muted />
                  <canvas ref="cameraCanvasRef" class="camera-overlay" :class="{ hidden: !cameraActive }" />
                  <div v-if="cameraActive" class="camera-hud">
                    <span class="hud-item fps">FPS {{ cameraFps }}</span>
                    <span class="hud-item">间隔 300ms</span>
                    <span class="hud-item">{{ cameraObjCount }} targets</span>
                    <span class="hud-item">{{ (confidence * 100).toFixed(0) }}%</span>
                    <span v-if="cameraStats.detection_time" class="hud-item">{{ (cameraStats.detection_time * 1000).toFixed(0) }}ms</span>
                  </div>
                  <div v-if="cameraActive" class="camera-rec-dot" />
                  <div v-if="!cameraActive" class="camera-placeholder">
                    <div class="camera-placeholder-icon">
                      <el-icon :size="48"><Camera /></el-icon>
                    </div>
                    <p class="camera-placeholder-text">点击按钮开启摄像头实时检测</p>
                    <p class="camera-placeholder-hint">系统将逐帧捕获画面并识别病虫害</p>
                  </div>
                </div>
                <div class="camera-controls">
                  <el-button
                    v-if="!cameraActive"
                    type="primary"
                    size="large"
                    @click="startCamera"
                  >
                    <el-icon><Camera /></el-icon>
                    开启摄像头
                  </el-button>
                  <el-button
                    v-else
                    type="danger"
                    size="large"
                    @click="stopCamera"
                  >
                    关闭摄像头
                  </el-button>
                </div>
              </div>
            </div>
            <DetectionPanel
              :modelStatus="modelStatus"
              :detectionResult="cameraPanelResult"
              :selectedName="popoverSelectedName"
              mode="camera"
              @generate-report="handleGenerateReport"
              @select-pest="handleSelectPest"
            />
          </div>
        </template>
      </div>
    </div>
    <PestDetailPopover
      v-if="popoverPest"
      :pest="popoverPest"
      :visible="popoverVisible"
      @close="popoverVisible = false"
      @go-guide="handleGoGuide"
    />

    <!-- 报告弹窗 -->
    <el-dialog v-model="reportVisible" title="检测报告" width="640px" destroy-on-close>
      <div v-if="reportData" class="report-content">
        <div class="report-header">
          <span class="report-mode">{{ { image: '图片检测', video: '视频检测', camera: '实时检测' }[reportData.mode] }}</span>
          <span class="report-model">模型: {{ reportData.model_version }}</span>
        </div>

        <!-- 图片模式报告 -->
        <template v-if="reportData.mode === 'image'">
          <div class="report-images">
            <div class="report-img-box">
              <span class="report-img-label">原图</span>
              <img :src="reportData.original_image" class="report-img" />
            </div>
            <div class="report-img-box">
              <span class="report-img-label">检测结果</span>
              <img :src="reportData.result_image" class="report-img" />
            </div>
          </div>
        </template>

        <!-- 视频模式报告 -->
        <template v-if="reportData.mode === 'video'">
          <video :src="reportData.result_video" controls class="report-video" />
          <div class="report-stats">
            <div class="report-stat"><span class="rs-val">{{ reportData.total_objects }}</span><span class="rs-label">检测目标</span></div>
            <div class="report-stat"><span class="rs-val">{{ reportData.processed_frames }}</span><span class="rs-label">处理帧数</span></div>
            <div class="report-stat"><span class="rs-val">{{ reportData.duration }}s</span><span class="rs-label">视频时长</span></div>
            <div class="report-stat"><span class="rs-val">{{ reportData.detection_time }}s</span><span class="rs-label">检测耗时</span></div>
          </div>
          <div v-if="Object.keys(reportData.summary).length" class="report-summary">
            <div class="report-section-title">病虫害统计</div>
            <div v-for="(count, name) in reportData.summary" :key="name" class="report-summary-item">
              <span>{{ name }}</span><span class="report-summary-count">{{ count }}</span>
            </div>
          </div>
        </template>

        <!-- 摄像头模式报告 -->
        <template v-if="reportData.mode === 'camera'">
          <div class="report-stats">
            <div class="report-stat"><span class="rs-val">{{ reportData.total_objects }}</span><span class="rs-label">累积物种</span></div>
            <div class="report-stat"><span class="rs-val">{{ reportData.detection_time ? (reportData.detection_time * 1000).toFixed(0) + 'ms' : '-' }}</span><span class="rs-label">检测耗时</span></div>
          </div>
        </template>

        <!-- 物种清单 -->
        <div v-if="reportData.boxes?.length" class="report-species">
          <div class="report-section-title">识别物种清单</div>
          <div v-for="(box, i) in reportData.boxes" :key="i" class="report-species-item">
            <span class="rs-name">{{ box.chinese_name || box.class_name }}</span>
            <span class="rs-conf">{{ (box.confidence * 100).toFixed(1) }}%</span>
          </div>
        </div>

        <div class="report-footer">
          <span>检测时间: {{ new Date().toLocaleString('zh-CN') }}</span>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="reportVisible = false; $router.push('/history')">查看检测记录</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElLoading } from "element-plus";
import {
  UploadFilled, Picture, Plus, VideoCamera, Setting,
  RefreshLeft, ArrowLeft, ArrowRight, WarningFilled, Camera,
} from "@element-plus/icons-vue";
import { detectSingleImage, detectBatchImages, detectVideo, detectFrame, getModels, getModelStatus, switchModel, getPestList } from "../api/detection";
import ImageCompare from "../components/ImageCompare.vue";
import DetectionPanel from "../components/DetectionPanel.vue";
import PestDetailPopover from "../components/PestDetailPopover.vue";

const router = useRouter();

const modes = [
  { key: "image", label: "图片检测", icon: Picture },
  { key: "video", label: "视频检测", icon: VideoCamera },
  { key: "camera", label: "实时检测", icon: Camera },
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
const lastImageFile = ref(null); // 用于重新检测
const lastVideoFile = ref(null);
const batchResults = ref([]);
const batchFiles = ref([]);
const currentIndex = ref(0);
const videoResult = ref(null);

const videoPanelResult = computed(() => {
  if (!videoResult.value) return null;
  const v = videoResult.value;
  const boxes = Object.entries(v.summary || {}).map(([class_name, count]) => ({
    class_name,
    chinese_name: class_name,
    count,
    confidence: 1,
  }));
  return {
    total_objects: v.total_objects,
    detection_time: v.detection_time,
    boxes,
  };
});

// 累积物种清单（仅添加模式，每 5s 更新一次最高置信度）
const cameraSpeciesMap = ref({});
const SPECIES_UPDATE_INTERVAL = 5000;
let _speciesTimerId = null;

function mergeSpeciesFromBoxes(boxes) {
  const map = { ...cameraSpeciesMap.value };
  for (const box of boxes) {
    const key = box.class_id ?? box.class_name;
    if (!map[key] || box.confidence > map[key].confidence) {
      map[key] = {
        class_id: box.class_id,
        class_name: box.class_name,
        chinese_name: box.chinese_name || "",
        confidence: box.confidence,
      };
    }
  }
  cameraSpeciesMap.value = map;
}

const cameraPanelResult = computed(() => {
  if (!cameraActive.value) return null;
  const species = Object.values(cameraSpeciesMap.value);
  if (species.length === 0) {
    return { total_objects: 0, detection_time: 0, boxes: [] };
  }
  return {
    total_objects: species.length,
    detection_time: cameraStats.value.detection_time,
    boxes: species.sort((a, b) => b.confidence - a.confidence),
  };
});

const singleInputRef = ref(null);
const batchInputRef = ref(null);
const videoInputRef = ref(null);

// 摄像头实时检测
const cameraActive = ref(false);
const cameraStream = ref(null);
const cameraVideoRef = ref(null);
const cameraCanvasRef = ref(null);
const cameraBoxes = ref([]);
const cameraStats = ref({ total_objects: 0, detection_time: 0, class_summary: {} });
const cameraLoopId = ref(null);
const cameraFps = ref(0);
const cameraObjCount = ref(0);
let _fpsFrames = [];
// 平滑稳定
let _smoothBoxes = [];       // 平滑后的框
let _lastDetectTime = 0;     // 上次成功检测时间
let _detectRunning = false;  // 防止并发
let _consecutiveErrors = 0;  // 连续错误计数
let _cameraLoopActive = false;
const SMOOTH_ALPHA = 0.6;    // EMA 平滑系数（越大越灵敏）
const PERSIST_MS = 600;      // 框滞留时间（ms）
const DETECT_INTERVAL = 300; // 检测间隔（ms）

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

// 图鉴数据
const pestDatabase = ref([]);

async function loadPestData() {
  try {
    const res = await getPestList();
    if (res.success) pestDatabase.value = res.data;
  } catch (e) {
    console.error("加载图鉴数据失败:", e);
  }
}

// 图鉴浮窗
const popoverVisible = ref(false);
const popoverPest = ref(null);
const popoverSelectedName = ref(null);

function handleSelectPest(name) {
  const match = pestDatabase.value.find(
    p => p.name === name || p.chinese_name === name
  );
  if (match) {
    popoverPest.value = match;
    popoverSelectedName.value = name;
    popoverVisible.value = true;
  } else {
    ElMessage.info("未找到该物种的图鉴信息");
  }
}

// 报告弹窗
const reportVisible = ref(false);
const reportData = ref(null);

function handleGenerateReport() {
  let data = null;
  if (activeMode.value === 'image' && detectionResult.value) {
    data = {
      mode: 'image',
      filename: detectionResult.value.filename || '单图检测',
      original_image: originalImage.value,
      result_image: resultImage.value,
      total_objects: detectionResult.value.total_objects,
      detection_time: detectionResult.value.detection_time,
      boxes: detectionResult.value.boxes || [],
      model_version: modelStatus.value.model_version || '-',
    };
  } else if (activeMode.value === 'video' && videoResult.value) {
    data = {
      mode: 'video',
      filename: '视频检测',
      result_video: videoResult.value.result_video_url,
      total_objects: videoResult.value.total_objects,
      duration: videoResult.value.duration,
      fps: videoResult.value.fps,
      processed_frames: videoResult.value.processed_frames,
      detection_time: videoResult.value.detection_time,
      summary: videoResult.value.summary || {},
      key_frames: videoResult.value.key_frames || [],
      model_version: modelStatus.value.model_version || '-',
    };
  } else if (activeMode.value === 'camera' && cameraActive.value) {
    const species = Object.values(cameraSpeciesMap.value);
    data = {
      mode: 'camera',
      filename: '实时检测',
      total_objects: species.length,
      detection_time: cameraStats.value.detection_time,
      boxes: species,
      model_version: modelStatus.value.model_version || '-',
    };
  }

  if (!data) {
    ElMessage.warning('暂无检测结果，请先进行检测');
    return;
  }

  reportData.value = data;
  reportVisible.value = true;
}

function handleRedetect() {
  if (activeMode.value === 'image' && lastImageFile.value) {
    performSingleDetection(lastImageFile.value);
  } else if (activeMode.value === 'video' && lastVideoFile.value) {
    performVideoDetection(lastVideoFile.value);
  } else {
    ElMessage.warning('暂无可重新检测的内容');
  }
}

function handleGoGuide() {
  popoverVisible.value = false;
  router.push("/guide");
}

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
  lastImageFile.value = null;
  if (originalImage.value) URL.revokeObjectURL(originalImage.value);
  originalImage.value = "";
};

const performSingleDetection = async (file) => {
  const loading = ElLoading.service({ lock: true, text: "正在检测中...", background: "rgba(0,0,0,0.7)" });
  try {
    isDetecting.value = true;
    resetDetection();
    lastImageFile.value = file;
    lastVideoFile.value = null;
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
    resetDetection();
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
    lastVideoFile.value = file;
    lastImageFile.value = null;
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

onMounted(() => { loadModels(); loadPestData(); });
onUnmounted(() => {
  if (originalImage.value) URL.revokeObjectURL(originalImage.value);
  stopCamera();
});

// === 摄像头实时检测 ===
const startCamera = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 640 },
        height: { ideal: 480 },
        frameRate: { ideal: 30 },
        facingMode: "environment",
      },
    });
    cameraStream.value = stream;
    cameraActive.value = true;
    cameraBoxes.value = [];
    cameraStats.value = { total_objects: 0, detection_time: 0, class_summary: {} };
    cameraSpeciesMap.value = {};
    _smoothBoxes = [];
    _fpsFrames = [];
    _detectRunning = false;
    _consecutiveErrors = 0;
    await new Promise(r => setTimeout(r, 200));
    if (cameraVideoRef.value) {
      cameraVideoRef.value.srcObject = stream;
      cameraVideoRef.value.play();
    }
    _cameraLoopActive = true;
    // 检测循环：固定 500ms 间隔（实时框绘制）
    cameraLoopId.value = setInterval(runFrameDetection, DETECT_INTERVAL);
    // 物种清单更新：每 5 秒合并一次
    _speciesTimerId = setInterval(() => {
      if (_smoothBoxes.length > 0) mergeSpeciesFromBoxes(_smoothBoxes);
    }, SPECIES_UPDATE_INTERVAL);
    // 获取摄像头实际帧率
    const videoTrack = stream.getVideoTracks()[0];
    const trackSettings = videoTrack.getSettings();
    cameraFps.value = trackSettings.frameRate || 30;
    // 绘制循环
    requestAnimationFrame(renderLoop);
  } catch (e) {
    handleCameraError(e);
  }
};

const stopCamera = () => {
  _cameraLoopActive = false;
  if (cameraLoopId.value) { clearInterval(cameraLoopId.value); cameraLoopId.value = null; }
  if (_speciesTimerId) { clearInterval(_speciesTimerId); _speciesTimerId = null; }
  if (cameraStream.value) { cameraStream.value.getTracks().forEach(t => t.stop()); cameraStream.value = null; }
  cameraActive.value = false;
  cameraBoxes.value = [];
  cameraFps.value = 0;
  cameraObjCount.value = 0;
  _smoothBoxes = [];
  _fpsFrames = [];
  _detectRunning = false;
  _consecutiveErrors = 0;
};

const handleCameraError = (error) => {
  console.error("摄像头错误:", error);
  switch (error.name) {
    case "NotAllowedError":
      ElMessage.error("摄像头权限被拒绝，请在浏览器设置中允许访问摄像头");
      break;
    case "NotFoundError":
      ElMessage.error("未检测到摄像头设备，请检查设备连接");
      break;
    case "NotReadableError":
      ElMessage.error("摄像头被其他应用占用，请关闭其他应用后重试");
      break;
    case "OverconstrainedError":
      ElMessage.error("摄像头不支持当前分辨率设置");
      break;
    default:
      ElMessage.error("无法访问摄像头，请检查设备和权限设置");
  }
  stopCamera();
};

// 前端绘制用渲染循环（rAF，持续绘制不断刷新画面和框）
let _renderActive = false;
function renderLoop() {
  if (!cameraActive.value) { _renderActive = false; return; }
  _renderActive = true;
  drawCameraBoxes();
  requestAnimationFrame(renderLoop);
}

// EMA 平滑：将新旧框按类别匹配，平滑坐标
function smoothUpdate(newBoxes) {
  const now = performance.now();
  const result = [];

  for (const nb of newBoxes) {
    // 查找最近的旧框（同类且 IoU > 0.3）
    let best = null, bestIoU = 0;
    for (const ob of _smoothBoxes) {
      if (ob.class_id !== nb.class_id) continue;
      const iou = computeIoU(nb, ob);
      if (iou > bestIoU) { bestIoU = iou; best = ob; }
    }

    if (best && bestIoU > 0.3) {
      // EMA 平滑坐标
      result.push({
        x1: best.x1 + (nb.x1 - best.x1) * SMOOTH_ALPHA,
        y1: best.y1 + (nb.y1 - best.y1) * SMOOTH_ALPHA,
        x2: best.x2 + (nb.x2 - best.x2) * SMOOTH_ALPHA,
        y2: best.y2 + (nb.y2 - best.y2) * SMOOTH_ALPHA,
        confidence: best.confidence + (nb.confidence - best.confidence) * SMOOTH_ALPHA,
        class_id: nb.class_id,
        class_name: nb.class_name,
        chinese_name: nb.chinese_name || best.chinese_name || "",
        lastSeen: now,
      });
    } else {
      result.push({ ...nb, lastSeen: now });
    }
  }

  // 保留滞留框（新帧没检测到但还在 PERSIST_MS 内）
  for (const ob of _smoothBoxes) {
    if (now - ob.lastSeen < PERSIST_MS) {
      const dominated = result.some(nb => nb.class_id === ob.class_id && computeIoU(nb, ob) > 0.3);
      if (!dominated) result.push(ob);
    }
  }

  _smoothBoxes = result;
  cameraBoxes.value = result;
  cameraObjCount.value = result.length;
}

function computeIoU(a, b) {
  const ix1 = Math.max(a.x1, b.x1), iy1 = Math.max(a.y1, b.y1);
  const ix2 = Math.min(a.x2, b.x2), iy2 = Math.min(a.y2, b.y2);
  const inter = Math.max(0, ix2 - ix1) * Math.max(0, iy2 - iy1);
  const ua = (a.x2 - a.x1) * (a.y2 - a.y1) + (b.x2 - b.x1) * (b.y2 - b.y1) - inter;
  return ua > 0 ? inter / ua : 0;
}

const MAX_CONSECUTIVE_ERRORS = 5;
// 复用离屏 canvas，避免每帧创建新元素
const _offscreenCanvas = document.createElement("canvas");
const _offscreenCtx = _offscreenCanvas.getContext("2d");

const runFrameDetection = async () => {
  if (!cameraVideoRef.value || !cameraActive.value || _detectRunning) return;
  _detectRunning = true;
  const now = performance.now();

  try {
    const video = cameraVideoRef.value;
    if (!video.videoWidth || !video.videoHeight) { _detectRunning = false; return; }
    // 降采样给后端：显示 640x480，上传 320x240
    _offscreenCanvas.width = Math.round(video.videoWidth / 2);
    _offscreenCanvas.height = Math.round(video.videoHeight / 2);
    _offscreenCtx.drawImage(video, 0, 0, _offscreenCanvas.width, _offscreenCanvas.height);
    const blob = await new Promise(r => _offscreenCanvas.toBlob(r, "image/jpeg", 0.5));
    if (!blob) { _detectRunning = false; return; }

    const formData = new FormData();
    formData.append("file", blob, "frame.jpg");
    formData.append("model_name", selectedModel.value);
    formData.append("conf", confidence.value);
    const res = await detectFrame(formData);
    if (res.success && res.data) {
      cameraStats.value = res.data;
      _lastDetectTime = now;
      _consecutiveErrors = 0;
      smoothUpdate(res.data.boxes);
    } else {
      _consecutiveErrors++;
    }
  } catch {
    _consecutiveErrors++;
  }

  // 连续错误超过阈值自动停止
  if (_consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
    ElMessage.error("检测连续失败，请检查网络或模型状态");
    stopCamera();
  }

  _detectRunning = false;
};

const COLORS = [
  "#48d1ad", "#327fe9", "#2ec76a", "#8a57e8", "#22b2e5",
  "#39c7ba", "#e86f30", "#8360e8", "#d5534f", "#3285e8",
  "#5cb84d", "#e39c25", "#4285f4", "#78b834", "#d94437",
  "#f4b400", "#ab47bc", "#00acc1", "#ff7043", "#7cb942",
];

const drawCameraBoxes = () => {
  if (!cameraVideoRef.value || !cameraCanvasRef.value) return;
  const video = cameraVideoRef.value;
  const canvas = cameraCanvasRef.value;
  const ctx = canvas.getContext("2d");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const vw = canvas.width;
  const vh = canvas.height;
  // 后端处理的是半分辨率，坐标需 ×2 映射回显示分辨率
  const scaleX = vw / Math.round(vw / 2);
  const scaleY = vh / Math.round(vh / 2);
  const lw = Math.max(2, Math.min(vw, vh) / 300);
  const fontSize = Math.max(12, Math.min(vw, vh) / 45);

  for (const box of cameraBoxes.value) {
    const x1 = box.x1 * scaleX, y1 = box.y1 * scaleY;
    const x2 = box.x2 * scaleX, y2 = box.y2 * scaleY;
    const color = COLORS[box.class_id % COLORS.length];

    // 半透明填充
    ctx.globalAlpha = 0.06;
    ctx.fillStyle = color;
    ctx.fillRect(x1, y1, x2 - x1, y2 - y1);
    ctx.globalAlpha = 1;

    // 圆角边框
    ctx.strokeStyle = color;
    ctx.lineWidth = lw;
    ctx.setLineDash([]);
    roundRect(ctx, x1, y1, x2 - x1, y2 - y1, 10);
    ctx.stroke();

    // 四角加粗装饰线
    const cl = Math.max(14, Math.min(x2 - x1, y2 - y1) * 0.18);
    ctx.lineWidth = lw + 2;
    ctx.beginPath();
    ctx.moveTo(x1, y1 + cl); ctx.lineTo(x1, y1); ctx.lineTo(x1 + cl, y1);
    ctx.moveTo(x2 - cl, y1); ctx.lineTo(x2, y1); ctx.lineTo(x2, y1 + cl);
    ctx.moveTo(x1, y2 - cl); ctx.lineTo(x1, y2); ctx.lineTo(x1 + cl, y2);
    ctx.moveTo(x2 - cl, y2); ctx.lineTo(x2, y2); ctx.lineTo(x2, y2 - cl);
    ctx.stroke();

    // 底部置信度条
    const barH = 4;
    const barW = (x2 - x1) * box.confidence;
    ctx.globalAlpha = 0.3;
    ctx.fillStyle = "#000";
    ctx.fillRect(x1, y2 - barH, x2 - x1, barH);
    ctx.globalAlpha = 1;
    ctx.fillStyle = color;
    ctx.fillRect(x1, y2 - barH, barW, barH);

    // 标签（带阴影）
    const label = `${box.class_name} ${(box.confidence * 100).toFixed(0)}%`;
    ctx.font = `600 ${fontSize}px sans-serif`;
    const tw = ctx.measureText(label).width + 14;
    const th = fontSize + 12;
    let lx = x1, ly = y1 - th - 2;
    if (ly < 0) ly = y2 + 2;

    // 阴影
    ctx.globalAlpha = 0.15;
    ctx.fillStyle = "#000";
    ctx.beginPath();
    ctx.roundRect(lx + 2, ly + 2, tw, th, 6);
    ctx.fill();
    // 背景
    ctx.globalAlpha = 0.92;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.roundRect(lx, ly, tw, th, 6);
    ctx.fill();
    ctx.globalAlpha = 1;
    // 文字
    ctx.fillStyle = "#fff";
    ctx.fillText(label, lx + 7, ly + th - 5);
  }
};

function roundRect(ctx, x, y, w, h, r) {
  r = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.arcTo(x + w, y, x + w, y + r, r);
  ctx.lineTo(x + w, y + h - r);
  ctx.arcTo(x + w, y + h, x + w - r, y + h, r);
  ctx.lineTo(x + r, y + h);
  ctx.arcTo(x, y + h, x, y + h - r, r);
  ctx.lineTo(x, y + r);
  ctx.arcTo(x, y, x + r, y, r);
  ctx.closePath();
}
</script>

<style scoped>
.detection-page { width: 100%; max-width: 1040px; margin: 0 auto; display: flex; flex-direction: column; padding-bottom: 24px; }

/* === 页头 === */
.page-header { margin-bottom: 24px; flex-shrink: 0; animation: fade-up 0.6s var(--ease-out-expo) both; }
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
  min-width: 0;
  background: #ffffff; border-radius: 14px; padding: 24px;
  display: flex; flex-direction: column;
  box-shadow: var(--card-shadow);
  border: 1px solid var(--border-color);
  transition: box-shadow 0.3s var(--ease-out-expo), transform 0.3s var(--ease-out-expo);
  animation: fade-up 0.6s var(--ease-out-expo) both;
  animation-delay: 0.15s;
}
.result-left:hover { box-shadow: var(--card-shadow-hover); transform: translateY(-2px); }

/* === 模式切换 === */
.mode-switch {
  display: flex;
  flex-direction: column;
  background: #f1f5f9;
  border-radius: 12px;
  padding: 4px;
  gap: 2px;
  animation: fade-up 0.6s var(--ease-out-expo) both;
  animation-delay: 0.1s;
}
.mode-btn {
  display: flex; align-items: center; gap: 8px; padding: 12px 14px;
  border: none; background: transparent; border-radius: 10px; cursor: pointer;
  font-size: 14px; font-weight: 500; color: var(--text-secondary);
  transition: all 0.2s ease; width: 100%;
  animation: fade-in 0.6s var(--ease-out-expo) both;
}
.mode-btn:nth-child(1) { animation-delay: 0.15s; }
.mode-btn:nth-child(2) { animation-delay: 0.2s; }
.mode-btn:nth-child(3) { animation-delay: 0.25s; }
.mode-btn:nth-child(4) { animation-delay: 0.3s; }
.mode-btn:hover { color: var(--text-primary); background: rgba(255,255,255,0.5); }
.mode-btn.active {
  color: var(--primary-color); background: #ffffff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

/* === 设置面板（内联） === */
.settings-inline {
  background: #ffffff; border-radius: 14px; padding: 18px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  animation: fade-up 0.6s var(--ease-out-expo) both;
  animation-delay: 0.2s;
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
  animation: fade-up 0.6s var(--ease-out-expo) both;
  animation-delay: 0.3s;
}
.model-info-item {
  display: flex; justify-content: space-between; align-items: flex-start;
  padding: 8px 0; border-bottom: 1px solid #f3f4f6;
}
.model-info-item:last-child { border-bottom: none; }
.model-info-label { font-size: 12px; color: var(--text-secondary); flex-shrink: 0; }
.model-info-value { font-size: 12px; font-weight: 500; color: var(--text-primary); text-align: right; margin-left: 8px; }
.model-option-desc { font-size: 11px; color: var(--text-secondary); margin-left: 8px; }
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
.batch-thumb.active { border-color: var(--primary-color); box-shadow: 0 0 0 2px rgba(180,83,9,0.15); }
.batch-thumb.failed { opacity: 0.5; }
.thumb-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.thumb-error { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: #ef4444; }
.thumb-count {
  position: absolute; bottom: 2px; right: 2px; font-size: 10px; font-weight: 600;
  background: rgba(180,83,9,0.9); color: #fff; padding: 1px 5px; border-radius: 4px;
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

/* === 实时摄像头 === */
.camera-view { display: flex; flex-direction: column; gap: 16px; }
.camera-container {
  position: relative; width: 100%; aspect-ratio: 4/3;
  border-radius: 12px; overflow: hidden; background: #1a1a2e;
}
.camera-video { width: 100%; height: 100%; object-fit: cover; display: block; }
.camera-overlay {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  pointer-events: none;
}
.camera-placeholder {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  color: #a0a0b8;
}
.camera-placeholder-icon {
  width: 80px; height: 80px; border-radius: 50%;
  background: rgba(255,255,255,0.06);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 16px;
}
.camera-placeholder-text { font-size: 15px; color: #d0d0e0; margin: 0 0 4px 0; }
.camera-placeholder-hint { font-size: 12px; color: #8080a0; margin: 0; }
.camera-controls { display: flex; justify-content: center; }
.hidden { display: none; }

/* 摄像头 HUD */
.camera-hud {
  position: absolute; top: 12px; left: 12px;
  display: flex; gap: 8px; z-index: 10;
}
.hud-item {
  padding: 4px 10px; border-radius: 6px;
  background: rgba(0, 0, 0, 0.6); color: #e0e0e0;
  font-size: 12px; font-weight: 500; font-variant-numeric: tabular-nums;
  backdrop-filter: blur(4px);
}
.hud-item.fps { color: #4ade80; font-weight: 700; }
.camera-rec-dot {
  position: absolute; top: 14px; right: 14px;
  width: 10px; height: 10px; border-radius: 50%;
  background: #ef4444; animation: blink 1.2s ease-in-out infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* 报告弹窗 */
.report-content { display: flex; flex-direction: column; gap: 16px; }
.report-header { display: flex; justify-content: space-between; align-items: center; }
.report-mode { font-size: 15px; font-weight: 600; color: var(--primary-color); }
.report-model { font-size: 12px; color: var(--text-secondary); }
.report-images { display: flex; gap: 12px; }
.report-img-box { flex: 1; min-width: 0; }
.report-img-label { display: block; font-size: 12px; color: var(--text-secondary); margin-bottom: 6px; }
.report-img { width: 100%; border-radius: 8px; object-fit: contain; max-height: 240px; background: #f3f4f6; }
.report-video { width: 100%; border-radius: 8px; background: #000; }
.report-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.report-stat { display: flex; flex-direction: column; align-items: center; padding: 10px 4px; background: #f9fafb; border-radius: 8px; }
.rs-val { font-size: 18px; font-weight: 700; color: var(--primary-color); }
.rs-label { font-size: 11px; color: var(--text-secondary); margin-top: 2px; }
.report-section-title { font-size: 13px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; }
.report-summary { display: flex; flex-direction: column; gap: 4px; }
.report-summary-item { display: flex; justify-content: space-between; padding: 5px 10px; background: #f9fafb; border-radius: 6px; font-size: 13px; }
.report-summary-count { font-weight: 600; color: var(--primary-color); }
.report-species { display: flex; flex-direction: column; gap: 4px; }
.report-species-item { display: flex; justify-content: space-between; padding: 5px 10px; background: #f9fafb; border-radius: 6px; }
.rs-name { font-size: 13px; color: var(--text-primary); }
.rs-conf { font-size: 12px; font-weight: 500; color: var(--primary-color); }
.report-footer { font-size: 11px; color: var(--text-secondary); text-align: right; padding-top: 8px; border-top: 1px solid #f3f4f6; }
</style>
