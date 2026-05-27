<template>
  <div class="panel-wrapper">
    <div class="cards-row">
      <div class="result-card">
        <div class="card-header">
          <el-icon><List /></el-icon>
          <span class="card-title">识别清单</span>
          <span v-if="detectionResult?.boxes?.length > 0" class="card-hint">点击物种查看详情</span>
        </div>
        <div v-if="!detectionResult || detectionResult.total_objects === 0" class="empty-state">
          <el-icon class="empty-icon"><CircleCheck /></el-icon>
          <p class="empty-text">未检测到病虫害</p>
          <p class="empty-desc">请上传农作物图片开始检测</p>
        </div>
        <div v-else class="detection-list">
          <div
            v-for="(sp, index) in uniqueSpecies"
            :key="sp.class_id ?? index"
            class="detection-item"
            :class="{ active: selectedName && selectedName === sp.class_name }"
            @click="$emit('select-pest', sp.class_name)"
          >
            <span class="item-name">{{ sp.chinese_name }}</span>
            <span v-if="sp.count > 1" class="item-count">{{ sp.count }}只</span>
            <span class="item-confidence">{{ (sp.maxConf * 100).toFixed(1) }}%</span>
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
            模型: {{ modelStatus.model_version || '-' }}
          </p>
        </div>
      </div>
    </div>

    <div class="action-cards">
      <div class="action-card" @click="$emit('redetect')">
        <el-icon class="action-icon"><Refresh /></el-icon>
        <span class="action-label">重新检测</span>
      </div>
      <div class="action-card action-card--primary">
        <el-icon class="action-icon"><Document /></el-icon>
        <span class="action-label">查看完整报告</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { List, CircleCheck, ChatDotRound, Refresh, Document } from "@element-plus/icons-vue";

const props = defineProps({
  modelStatus: { type: Object, default: () => ({}) },
  detectionResult: { type: Object, default: null },
  selectedName: { type: String, default: null },
});

defineEmits(["redetect", "select-pest"]);

const uniqueSpecies = computed(() => {
  if (!props.detectionResult?.boxes?.length) return [];
  const map = {};
  for (const box of props.detectionResult.boxes) {
    const key = box.class_id ?? box.class_name;
    if (!map[key]) {
      map[key] = {
        class_name: box.class_name,
        chinese_name: box.chinese_name || box.class_name,
        count: box.count || 1,
        maxConf: box.confidence,
        class_id: box.class_id,
      };
    } else {
      map[key].count += box.count || 1;
      map[key].maxConf = Math.max(map[key].maxConf, box.confidence);
    }
  }
  return Object.values(map).sort((a, b) => b.maxConf - a.maxConf);
});
</script>

<style scoped>
.panel-wrapper {
  width: 100%; display: flex; flex-direction: column; gap: 12px;
  flex: 1; min-height: 0;
  animation: fade-up 0.6s var(--ease-out-expo) both;
}

.cards-row { display: flex; gap: 12px; flex: 1; min-height: 0; }
.cards-row .result-card { flex: 1; min-width: 0; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }

.result-card {
  background-color: #ffffff; border-radius: 12px; padding: 14px;
  box-shadow: var(--card-shadow); border: 1px solid var(--border-color);
  transition: box-shadow 0.3s var(--ease-out-expo), transform 0.3s var(--ease-out-expo);
  animation: fade-up 0.6s var(--ease-out-expo) both;
  overflow: hidden;
}
.result-card:nth-child(1) { animation-delay: 0.1s; }
.result-card:nth-child(2) { animation-delay: 0.2s; }
.result-card:hover { box-shadow: var(--card-shadow-hover); transform: translateY(-2px); }

.card-header { display: flex; align-items: center; margin-bottom: 10px; flex-shrink: 0; }
.card-header .el-icon { font-size: 15px; color: var(--primary-color); margin-right: 6px; }
.card-title { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.card-hint { font-size: 11px; color: var(--text-secondary); margin-left: auto; }

.empty-state { display: flex; flex-direction: column; align-items: center; padding: 20px 0; }
.empty-icon { font-size: 28px; color: var(--success-color); margin-bottom: 6px; animation: pulse-glow 2.5s ease-in-out infinite; }
.empty-text { font-size: 13px; font-weight: 500; color: var(--text-primary); margin-bottom: 2px; }
.empty-desc { font-size: 12px; color: var(--text-secondary); }

.detection-list { display: flex; flex-direction: column; gap: 4px; flex: 1; min-height: 0; overflow-y: auto; }
.detection-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 5px 10px; background-color: #f9fafb; border-radius: 6px; cursor: pointer;
  transition: background-color 0.2s ease, transform 0.2s var(--ease-out-expo);
  animation: fade-in 0.6s var(--ease-out-expo) both;
}
.detection-item:nth-child(1) { animation-delay: 0.3s; }
.detection-item:nth-child(2) { animation-delay: 0.4s; }
.detection-item:nth-child(3) { animation-delay: 0.5s; }
.detection-item:nth-child(4) { animation-delay: 0.6s; }
.detection-item:nth-child(5) { animation-delay: 0.7s; }
.detection-item:hover { background-color: #fef9ef; transform: translateX(2px); }
.detection-item.active { background-color: #fef3c7; border-left: 3px solid var(--primary-color); }

.item-name { font-size: 13px; color: var(--text-primary); }
.item-confidence { font-size: 12px; font-weight: 500; color: var(--primary-color); }
.item-count { font-size: 12px; font-weight: 600; color: #8b5cf6; }

.diagnosis-content { font-size: 12px; color: var(--text-secondary); line-height: 1.5; flex: 1; min-height: 0; overflow-y: auto; }
.diagnosis-content p { margin: 0; }

.action-cards { display: flex; gap: 10px; flex-shrink: 0; animation: fade-up 0.6s var(--ease-out-expo) both; animation-delay: 0.3s; }
.action-card {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 16px 0; background: #ffffff; border-radius: 12px; cursor: pointer;
  transition: box-shadow 0.3s var(--ease-out-expo), transform 0.3s var(--ease-out-expo);
  box-shadow: var(--card-shadow); border: 1px solid var(--border-color);
}
.action-card:hover { box-shadow: var(--card-shadow-hover); transform: translateY(-2px); }
.action-card:active { transform: scale(0.97); box-shadow: var(--card-shadow-active); }
.action-card--primary { background: linear-gradient(135deg, #b45309, #d97706); border-color: #b45309; }
.action-card--primary .action-icon,
.action-card--primary .action-label { color: #ffffff; }
.action-card--primary:hover { box-shadow: 0 4px 14px rgba(180,83,9,0.25); }

.action-icon { font-size: 16px; color: var(--primary-color); transition: transform 0.3s var(--ease-spring); }
.action-card:hover .action-icon { transform: scale(1.1); }
.action-card--primary:hover .action-icon { transform: rotate(-10deg) scale(1.1); }
.action-label { font-size: 13px; font-weight: 600; color: var(--text-primary); }
</style>
