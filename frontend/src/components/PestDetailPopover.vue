<template>
  <Teleport to="body">
    <div v-if="visible" class="popover-overlay" tabindex="-1" @click.self="$emit('close')" @keydown.escape="$emit('close')">
      <div class="popover-card">
        <div class="popover-header">
          <div class="header-left">
            <h2 class="popover-name">{{ pest.chinese_name }}</h2>
            <span v-if="pest.category" class="popover-badge">{{ pest.category }}</span>
            <span v-if="pest.pest_type" class="popover-badge type-badge">{{ pest.pest_type }}</span>
          </div>
          <button class="popover-close" @click="$emit('close')">
            <el-icon><Close /></el-icon>
          </button>
        </div>

        <p class="popover-sci" v-if="pest.scientific_name">
          <el-icon><PriceTag /></el-icon> {{ pest.scientific_name }}
        </p>
        <p class="popover-taxonomy" v-if="pest.order">
          {{ pest.order }}<span v-if="pest.family"> · {{ pest.family }}</span>
        </p>
        <p class="popover-desc">{{ pest.description }}</p>

        <div class="popover-sections">
          <div class="section" v-if="pest.host_plants">
            <div class="section-icon" style="background:#22c55e"><el-icon><Sunrise /></el-icon></div>
            <div class="section-body">
              <h4>寄主植物</h4>
              <p>{{ pest.host_plants }}</p>
            </div>
          </div>
          <div class="section" v-if="pest.damage_symptoms">
            <div class="section-icon" style="background:#ef4444"><el-icon><Warning /></el-icon></div>
            <div class="section-body">
              <h4>危害症状</h4>
              <p>{{ pest.damage_symptoms }}</p>
            </div>
          </div>
          <div class="section" v-if="pest.control_methods">
            <div class="section-icon" style="background:#3b82f6"><el-icon><FirstAidKit /></el-icon></div>
            <div class="section-body">
              <h4>防治方法</h4>
              <p>{{ pest.control_methods }}</p>
            </div>
          </div>
          <div class="section" v-if="pest.occurrence_period">
            <div class="section-icon" style="background:#f59e0b"><el-icon><Clock /></el-icon></div>
            <div class="section-body">
              <h4>发生时期</h4>
              <p>{{ pest.occurrence_period }}</p>
            </div>
          </div>
          <div class="section" v-if="pest.distribution">
            <div class="section-icon" style="background:#06b6d4"><el-icon><Location /></el-icon></div>
            <div class="section-body">
              <h4>分布范围</h4>
              <p>{{ pest.distribution }}</p>
            </div>
          </div>
        </div>

        <div class="popover-actions">
          <el-button type="primary" size="small" @click="$emit('go-guide')">
            查看完整图鉴
          </el-button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { Close, PriceTag, Sunrise, Warning, FirstAidKit, Clock, Location } from "@element-plus/icons-vue";

defineProps({
  pest: { type: Object, required: true },
  visible: { type: Boolean, default: false },
});

defineEmits(["close", "go-guide"]);
</script>

<style scoped>
.popover-overlay {
  position: fixed; inset: 0; z-index: 2000;
  background: rgba(0, 0, 0, 0.35);
  display: flex; align-items: center; justify-content: center;
  animation: fade-in 0.2s ease;
}
.popover-card {
  width: 480px; max-height: 80vh; background: #fff;
  border-radius: 16px; padding: 24px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.18);
  overflow-y: auto;
  animation: slide-up 0.25s var(--ease-out-expo);
}
@keyframes slide-up {
  from { opacity: 0; transform: translateY(24px); }
  to { opacity: 1; transform: translateY(0); }
}
.popover-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 8px;
}
.header-left { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.popover-name { font-size: 20px; font-weight: 700; margin: 0; color: var(--text-primary); }
.popover-badge {
  font-size: 11px; font-weight: 600; color: #fff;
  padding: 2px 8px; border-radius: 20px;
  background: var(--primary-color);
}
.type-badge { background: #8b5cf6; }
.popover-close {
  border: none; background: none; cursor: pointer;
  font-size: 20px; color: var(--text-secondary);
  padding: 4px; border-radius: 6px;
  transition: background 0.15s;
}
.popover-close:hover { background: #f3f4f6; }
.popover-sci {
  font-size: 13px; color: var(--text-secondary); margin: 4px 0;
  display: flex; align-items: center; gap: 4px;
}
.popover-sci .el-icon { font-size: 13px; }
.popover-taxonomy {
  font-size: 12px; color: var(--text-tertiary, #9ca3af); margin: 2px 0 8px;
}
.popover-desc {
  font-size: 13px; color: var(--text-secondary); line-height: 1.6;
  margin: 0 0 16px; padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}
.popover-sections { display: flex; flex-direction: column; gap: 14px; margin-bottom: 20px; }
.section { display: flex; gap: 12px; }
.section-icon {
  width: 32px; height: 32px; border-radius: 10px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 15px;
}
.section-body h4 { font-size: 13px; font-weight: 600; color: var(--text-primary); margin: 0 0 4px; }
.section-body p { font-size: 12px; color: var(--text-secondary); line-height: 1.6; margin: 0; }
.popover-actions {
  display: flex; justify-content: flex-end; gap: 10px;
  padding-top: 16px; border-top: 1px solid var(--border-color);
}
</style>
