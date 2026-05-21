<template>
  <div class="detection-page">
    <div class="page-header">
      <h1 class="page-title">上传农作物图片，快速识别病虫害</h1>
      <p class="page-subtitle">支持叶斑病 / 锈病 / 白粉病 / 蚜虫 / 毛虫等多种病虫害检测</p>
    </div>

    <div class="model-selector">
      <el-select v-model="selectedModel" style="width: 200px" @change="handleModelSwitch" :loading="modelsLoading">
        <el-option
          v-for="m in availableModels"
          :key="m.filename"
          :label="`${m.version} (${m.size_mb}MB)`"
          :value="m.filename"
        />
      </el-select>
    </div>

    <FunctionTabs
      ref="functionTabsRef"
      :activeTab="activeTab"
      @tabClick="handleTabClick"
      @fileChange="handleFileChange"
    />

    <div class="main-content">
      <ImageCompare
        :originalImage="originalImage"
        :resultImage="resultImage"
        :hasResult="!!detectionResult"
        :compareMode="compareMode"
        @update:compareMode="compareMode = $event"
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
import { detectSingleImage, getModels, getModelStatus, switchModel } from "../api/detection";
import FunctionTabs from "../components/FunctionTabs.vue";
import ImageCompare from "../components/ImageCompare.vue";
import DetectionPanel from "../components/DetectionPanel.vue";

const selectedModel = ref("");
const activeTab = ref("single");
const compareMode = ref("side");
const originalImage = ref("");
const resultImage = ref("");
const detectionResult = ref(null);
const isDetecting = ref(false);
const availableModels = ref([]);
const modelsLoading = ref(false);
const modelStatus = ref({});
const functionTabsRef = ref(null);

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
    if (tabKey === "single") await performSingleDetection(files[0]);
  }
  setTimeout(() => { event.target.value = ''; }, 0);
};

const performSingleDetection = async (file) => {
  const loading = ElLoading.service({ lock: true, text: "正在检测中...", background: "rgba(0, 0, 0, 0.7)" });
  try {
    isDetecting.value = true;
    const formData = new FormData();
    formData.append("file", file);
    formData.append("model_name", selectedModel.value);
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

const handleRedetect = () => {
  const refs = functionTabsRef.value?.fileInputRefs;
  if (refs?.["single"]) refs["single"].click();
};

onMounted(loadModels);
onUnmounted(() => { if (originalImage.value) URL.revokeObjectURL(originalImage.value); });
</script>

<style scoped>
.detection-page { width: 100%; position: relative; }
.page-header { margin-bottom: 32px; }
.page-title { font-size: 28px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; }
.page-subtitle { font-size: 14px; color: var(--text-secondary); }
.model-selector { position: absolute; top: 0; right: 0; z-index: 10; }
.main-content { display: flex; gap: 24px; }
</style>
