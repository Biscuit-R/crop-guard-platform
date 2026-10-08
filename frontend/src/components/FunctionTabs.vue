<template>
  <div class="function-tabs">
    <div
      v-for="tab in tabs"
      :key="tab.key"
      class="function-tab"
      :class="{ active: activeTab === tab.key }"
      @click="$emit('tabClick', tab.key)"
    >
      <input
        type="file"
        :accept="tab.accept"
        :multiple="tab.multiple"
        class="file-input"
        :ref="(el) => setRef(tab.key, el)"
        @change="$emit('fileChange', $event, tab.key)"
        @click.stop
      />
      <el-icon :size="18" class="tab-icon"><component :is="tab.icon" /></el-icon>
      <div class="tab-content">
        <span class="tab-text">{{ tab.name }}</span>
        <span class="tab-desc">{{ tab.desc }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Picture, Plus, Folder, Monitor } from "@element-plus/icons-vue";

defineProps({
  activeTab: { type: String, default: "single" },
});

defineEmits(["tabClick", "fileChange"]);

const tabs = [
  { key: "single", name: "单图检测", desc: "快速识别一张图片", icon: Picture, accept: "image/*", multiple: false },
  { key: "batch", name: "批量检测", desc: "一次处理多张图片", icon: Plus, accept: "image/*", multiple: true },
  { key: "folder", name: "文件夹", desc: "上传整个文件夹", icon: Folder, accept: "image/*", multiple: true },
  { key: "video", name: "视频检测", desc: "上传视频自动分析", icon: Monitor, accept: "video/*", multiple: false },
];

const fileInputRefs = {};
const setRef = (key, el) => { if (el) fileInputRefs[key] = el; };

defineExpose({ fileInputRefs });
</script>

<style scoped>
.function-tabs { display: flex; gap: 12px; margin-bottom: 24px; }

.function-tab {
  flex: 1; display: flex; align-items: center; padding: 16px 20px;
  background-color: #ffffff; border-radius: 12px; cursor: pointer;
  transition: all 0.2s; border: 2px solid transparent; position: relative; overflow: hidden;
}
.file-input {
  position: absolute; width: 100%; height: 100%; opacity: 0; cursor: pointer; z-index: 10;
}
.function-tab:hover { background-color: var(--primary-light); }
.function-tab.active { background-color: var(--primary-light); border-color: var(--primary-color); }
.tab-icon { font-size: 18px; color: var(--primary-color); margin-right: 12px; flex-shrink: 0; }
.tab-content { display: flex; flex-direction: column; }
.tab-text { font-size: 14px; font-weight: 600; color: var(--text-primary); line-height: 1.4; }
.tab-desc { font-size: 12px; color: var(--text-secondary); line-height: 1.4; }
</style>
