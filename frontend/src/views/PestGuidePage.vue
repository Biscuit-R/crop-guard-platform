<template>
  <div class="pest-guide-page">
    <div class="page-header">
      <h1 class="page-title">病虫害图鉴</h1>
      <p class="page-subtitle">平台支持检测的 {{ totalPests }} 种病虫害详细信息</p>
    </div>

    <div class="search-bar">
      <el-input v-model="searchQuery" placeholder="搜索害虫名称、学名、寄主植物..." class="search-input">
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <div class="search-stats" v-if="searchQuery">
        找到 {{ displayPests.length }} 个结果
      </div>
    </div>

    <!-- 四维筛选器 -->
    <div class="filter-panel">
      <div
        v-for="dim in filterDimensions"
        :key="dim.key"
        class="filter-group"
        :class="{ expanded: expandedDims[dim.key] }"
      >
        <div class="filter-header" @click="toggleDim(dim.key)">
          <span class="filter-label">{{ dim.label }}</span>
          <span v-if="activeFilters[dim.key].length" class="filter-active-count">
            {{ activeFilters[dim.key].length }}
          </span>
          <span class="filter-summary" v-if="activeFilters[dim.key].length">
            {{ activeFilters[dim.key].join('、') }}
          </span>
          <el-icon class="filter-arrow"><ArrowDown /></el-icon>
        </div>
        <transition name="slide">
          <div v-if="expandedDims[dim.key]" class="filter-options">
            <div
              class="filter-chip"
              :class="{ active: activeFilters[dim.key].length === 0 }"
              @click="clearFilter(dim.key)"
            >
              全部
            </div>
            <div
              v-for="opt in dim.options"
              :key="opt.value"
              class="filter-chip"
              :class="{ active: activeFilters[dim.key].includes(opt.value) }"
              @click="toggleFilter(dim.key, opt.value)"
            >
              {{ opt.label }}
              <span class="chip-count">{{ opt.count }}</span>
            </div>
          </div>
        </transition>
      </div>
    </div>

    <!-- 害虫卡片网格 -->
    <div class="pest-grid" v-loading="loading">
      <div
        v-for="pest in displayPests"
        :key="pest.id"
        class="pest-card"
        @click="showDetail(pest)"
      >
        <div class="card-top">
          <div class="card-badge" :style="{ background: getCategoryColor(pest.category) }">
            {{ pest.category }}
          </div>
          <div v-if="pest.pest_type" class="card-badge type">
            {{ pest.pest_type }}
          </div>
        </div>
        <div class="card-body">
          <h3 class="card-name">{{ pest.chinese_name }}</h3>
          <p class="card-sci" v-if="pest.scientific_name">{{ pest.scientific_name }}</p>
          <p class="card-desc">{{ pest.description }}</p>
        </div>
        <div class="card-footer">
          <span class="card-host" v-if="pest.host_plants">
            <el-icon><Star /></el-icon>
            {{ pest.host_plants.split('、')[0] }}{{ pest.host_plants.includes('、') ? ' 等' : '' }}
          </span>
          <el-icon class="card-arrow"><ArrowRight /></el-icon>
        </div>
      </div>
    </div>

    <div v-if="!loading && displayPests.length === 0" class="empty-state">
      <el-icon :size="64" class="empty-icon"><Search /></el-icon>
      <p class="empty-text">未找到匹配的病虫害</p>
    </div>

    <!-- 详情抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="selectedPest?.chinese_name || '详情'"
      size="520px"
      direction="rtl"
      :destroy-on-close="true"
    >
      <div v-if="selectedPest" class="detail-view">
        <div class="detail-title-row">
          <h2 class="detail-name">{{ selectedPest.chinese_name }}</h2>
          <span class="detail-badge" :style="{ background: getCategoryColor(selectedPest.category) }">
            {{ selectedPest.category }}
          </span>
          <span v-if="selectedPest.pest_type" class="detail-badge type-badge">
            {{ selectedPest.pest_type }}
          </span>
        </div>
        <p class="detail-sci" v-if="selectedPest.scientific_name">
          <el-icon><PriceTag /></el-icon> {{ selectedPest.scientific_name }}
        </p>
        <p class="detail-taxonomy" v-if="selectedPest.order || selectedPest.family">
          {{ selectedPest.order }}<span v-if="selectedPest.family"> · {{ selectedPest.family }}</span>
        </p>
        <p class="detail-intro">{{ selectedPest.description }}</p>

        <div class="detail-sections">
          <div class="detail-section" v-if="selectedPest.host_plants">
            <div class="section-icon" style="background:#22c55e"><el-icon><Sunrise /></el-icon></div>
            <div class="section-content">
              <h4>寄主植物</h4>
              <p>{{ selectedPest.host_plants }}</p>
            </div>
          </div>
          <div class="detail-section" v-if="selectedPest.morphology">
            <div class="section-icon" style="background:#8b5cf6"><el-icon><View /></el-icon></div>
            <div class="section-content">
              <h4>形态特征</h4>
              <p>{{ selectedPest.morphology }}</p>
            </div>
          </div>
          <div class="detail-section" v-if="selectedPest.damage_symptoms">
            <div class="section-icon" style="background:#ef4444"><el-icon><Warning /></el-icon></div>
            <div class="section-content">
              <h4>危害症状</h4>
              <p>{{ selectedPest.damage_symptoms }}</p>
            </div>
          </div>
          <div class="detail-section" v-if="selectedPest.occurrence_period">
            <div class="section-icon" style="background:#f59e0b"><el-icon><Clock /></el-icon></div>
            <div class="section-content">
              <h4>发生时期</h4>
              <p>{{ selectedPest.occurrence_period }}</p>
            </div>
          </div>
          <div class="detail-section" v-if="selectedPest.control_methods">
            <div class="section-icon" style="background:#3b82f6"><el-icon><FirstAidKit /></el-icon></div>
            <div class="section-content">
              <h4>防治方法</h4>
              <p>{{ selectedPest.control_methods }}</p>
            </div>
          </div>
          <div class="detail-section" v-if="selectedPest.distribution">
            <div class="section-icon" style="background:#06b6d4"><el-icon><Location /></el-icon></div>
            <div class="section-content">
              <h4>分布范围</h4>
              <p>{{ selectedPest.distribution }}</p>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import {
  Search, Star, ArrowRight, ArrowDown, Warning, FirstAidKit,
  Sunrise, View, Clock, Location, PriceTag,
} from "@element-plus/icons-vue";
import { getPestList } from "../api/detection";

const searchQuery = ref("");
const loading = ref(false);
const allPests = ref([]);
const drawerVisible = ref(false);
const selectedPest = ref(null);
const expandedDims = ref({});

// 四维筛选状态：每个维度支持多选
const activeFilters = ref({
  category: [],
  pest_type: [],
  region: [],
  season: [],
});

// 所有可能的季节标签（因为一条数据可能有"春季、夏季"）
const SEASON_LABELS = ["春季", "夏季", "秋季", "冬季", "全年"];

function toggleDim(key) {
  expandedDims.value[key] = !expandedDims.value[key];
}

function toggleFilter(dim, value) {
  const arr = activeFilters.value[dim];
  const idx = arr.indexOf(value);
  if (idx >= 0) arr.splice(idx, 1);
  else arr.push(value);
}

function clearFilter(dim) {
  activeFilters.value[dim] = [];
}

const CATEGORY_COLORS = {
  "水稻害虫": "#22c55e", "柑橘害虫": "#f59e0b", "苜蓿害虫": "#84cc16",
  "甜菜害虫": "#ef4444", "芒果害虫": "#f97316", "小麦害虫": "#eab308",
  "葡萄害虫": "#a855f7", "夜蛾类": "#6366f1", "蚜虫类": "#14b8a6",
  "其他害虫": "#64748b", "地下害虫": "#78716c", "蝶蛾类": "#ec4899",
  "玉米害虫": "#06b6d4", "甲虫类": "#d946ef", "螨类害虫": "#dc2626",
  "温室害虫": "#0ea5e9",
};

function getCategoryColor(cat) {
  return CATEGORY_COLORS[cat] || "#6b7280";
}

// 统计筛选维度选项
function countByField(list, field) {
  const map = {};
  for (const p of list) {
    const v = p[field];
    if (v) map[v] = (map[v] || 0) + 1;
  }
  return Object.entries(map)
    .map(([value, count]) => ({ value, label: value, count }))
    .sort((a, b) => b.count - a.count);
}

function countBySeason(list) {
  const map = {};
  for (const p of list) {
    if (!p.season) continue;
    for (const s of p.season.split("、")) {
      map[s] = (map[s] || 0) + 1;
    }
  }
  return SEASON_LABELS
    .filter((s) => map[s])
    .map((s) => ({ value: s, label: s, count: map[s] }));
}

// 四个筛选维度定义
const filterDimensions = computed(() => {
  const src = searchQuery.value ? searchResult.value : allPests.value;
  return [
    { key: "category", label: "寄主植物", options: countByField(src, "category") },
    { key: "pest_type", label: "害虫种类", options: countByField(src, "pest_type") },
    { key: "region", label: "分布范围", options: countByField(src, "region") },
    { key: "season", label: "发生季节", options: countBySeason(src) },
  ];
});

// 搜索结果（不含筛选）
const searchResult = computed(() => {
  if (!searchQuery.value) return allPests.value;
  const q = searchQuery.value.toLowerCase();
  return allPests.value.filter(
    (p) =>
      (p.chinese_name && p.chinese_name.toLowerCase().includes(q)) ||
      (p.scientific_name && p.scientific_name.toLowerCase().includes(q)) ||
      (p.description && p.description.toLowerCase().includes(q)) ||
      (p.host_plants && p.host_plants.toLowerCase().includes(q))
  );
});

// 最终展示列表：搜索 + 四维筛选
const displayPests = computed(() => {
  let list = searchResult.value;
  const f = activeFilters.value;

  if (f.category.length) {
    list = list.filter((p) => f.category.includes(p.category));
  }
  if (f.pest_type.length) {
    list = list.filter((p) => f.pest_type.includes(p.pest_type));
  }
  if (f.region.length) {
    list = list.filter((p) => f.region.includes(p.region));
  }
  if (f.season.length) {
    list = list.filter((p) => {
      if (!p.season) return false;
      const tags = p.season.split("、");
      return tags.some((s) => f.season.includes(s));
    });
  }
  return list;
});

const totalPests = computed(() => allPests.value.length);

function showDetail(pest) {
  selectedPest.value = pest;
  drawerVisible.value = true;
}

async function fetchPests() {
  loading.value = true;
  try {
    const res = await getPestList();
    if (res.success) allPests.value = res.data;
  } catch (e) {
    console.error("获取病虫害列表失败:", e);
  } finally {
    loading.value = false;
  }
}

onMounted(fetchPests);
</script>

<style scoped lang="scss">
.pest-guide-page {
  width: 100%; max-width: 1040px; margin: 0 auto; padding-bottom: 24px;

  .page-header {
    margin-bottom: 20px;
    animation: fade-up 0.6s var(--ease-out-expo) both;
    .page-title { font-size: 24px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
    .page-subtitle { font-size: 14px; color: var(--text-secondary); margin: 0; }
  }

  .search-bar {
    display: flex; align-items: center; gap: 16px; margin-bottom: 16px;
    animation: fade-up 0.6s var(--ease-out-expo) both; animation-delay: 0.08s;
    .search-input { max-width: 360px; }
    .search-stats { font-size: 13px; color: var(--text-secondary); }
  }

  /* === 四维筛选器 === */
  .filter-panel {
    display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 20px;
    align-items: start;
    animation: fade-up 0.6s var(--ease-out-expo) both; animation-delay: 0.12s;
  }

  .filter-group {
    background: var(--surface); border-radius: 10px;
    border: 1px solid var(--border-color); overflow: hidden;
    box-shadow: var(--card-shadow);
    transition: box-shadow 0.2s ease;
    &.expanded { box-shadow: var(--card-shadow-hover); }
  }

  .filter-header {
    display: flex; align-items: center; gap: 8px;
    padding: 10px 14px; cursor: pointer;
    transition: background 0.15s ease;
    &:hover { background: var(--primary-light); }
    .filter-label {
      font-size: 13px; font-weight: 600; color: var(--text-primary);
      white-space: nowrap;
    }
    .filter-active-count {
      min-width: 18px; height: 18px; padding: 0 5px;
      border-radius: 9px; background: var(--primary-color); color: #fff;
      font-size: 11px; font-weight: 600;
      display: inline-flex; align-items: center; justify-content: center;
    }
    .filter-summary {
      font-size: 12px; color: var(--text-secondary);
      overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
      flex: 1; min-width: 0;
    }
    .filter-arrow {
      font-size: 14px; color: var(--text-secondary); flex-shrink: 0;
      transition: transform 0.25s ease;
    }
    .expanded & .filter-arrow { transform: rotate(180deg); }
  }

  .filter-options {
    display: flex; flex-wrap: wrap; gap: 6px;
    padding: 0 14px 12px;
  }

  .filter-chip {
    padding: 4px 12px; border-radius: 14px; font-size: 12px;
    background: var(--bg-color); color: var(--text-secondary);
    border: 1px solid var(--border-color); cursor: pointer;
    transition: all 0.15s ease; white-space: nowrap;
    .chip-count { font-size: 10px; margin-left: 2px; opacity: 0.6; }
    &:hover { border-color: var(--primary-color); color: var(--text-primary); }
    &.active {
      background: var(--primary-color); color: #fff;
      border-color: var(--primary-color);
      .chip-count { opacity: 0.9; }
    }
  }

  .slide-enter-active, .slide-leave-active {
    transition: all 0.2s ease; overflow: hidden;
  }
  .slide-enter-from, .slide-leave-to {
    max-height: 0; opacity: 0; padding-top: 0; padding-bottom: 0;
  }
  .slide-enter-to, .slide-leave-from {
    max-height: 200px; opacity: 1;
  }

  /* === 卡片网格 === */
  .pest-grid {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;
    min-height: 200px;

    .pest-card {
      background: var(--surface); border-radius: 12px; border: 1px solid var(--border-color);
      box-shadow: var(--card-shadow); cursor: pointer; overflow: hidden;
      display: flex; flex-direction: column;
      transition: box-shadow 0.25s ease, transform 0.25s var(--ease-out-expo);
      animation: fade-up 0.5s var(--ease-out-expo) both;

      &:hover {
        box-shadow: var(--card-shadow-hover); transform: translateY(-3px);
        .card-arrow { transform: translateX(3px); color: var(--primary-color); }
      }

      .card-top {
        padding: 10px 14px 0;
        display: flex; gap: 6px; flex-wrap: wrap;
        .card-badge {
          display: inline-block; padding: 2px 10px; border-radius: 12px;
          font-size: 11px; color: #fff; font-weight: 500;
        }
        .card-badge.type { background: var(--text-secondary); opacity: 0.7; }
      }

      .card-body {
        padding: 10px 14px; flex: 1;
        .card-name {
          font-size: 15px; font-weight: 600; color: var(--text-primary);
          margin: 0 0 4px; line-height: 1.3;
        }
        .card-sci {
          font-size: 11px; color: var(--text-secondary); font-style: italic;
          margin: 0 0 6px;
        }
        .card-desc {
          font-size: 12px; color: var(--text-secondary); margin: 0;
          line-height: 1.5;
          display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
          overflow: hidden;
        }
      }

      .card-footer {
        padding: 8px 14px; border-top: 1px solid var(--border-color);
        display: flex; align-items: center; justify-content: space-between;
        .card-host {
          font-size: 11px; color: var(--text-secondary);
          display: flex; align-items: center; gap: 3px;
        }
        .card-arrow {
          font-size: 14px; color: var(--text-secondary);
          transition: transform 0.2s ease, color 0.2s ease;
        }
      }
    }
  }

  .empty-state {
    display: flex; flex-direction: column; align-items: center; padding: 60px 0;
    .empty-icon { color: #9ca3af; margin-bottom: 16px; }
    .empty-text { font-size: 15px; color: var(--text-secondary); }
  }
}

/* Detail drawer */
.detail-view {
  .detail-title-row {
    display: flex; align-items: center; gap: 10px; margin-bottom: 6px; flex-wrap: wrap;
    .detail-name { font-size: 22px; font-weight: 700; color: var(--text-primary); margin: 0; }
    .detail-badge {
      padding: 3px 12px; border-radius: 14px; font-size: 12px;
      color: #fff; font-weight: 500; flex-shrink: 0;
    }
    .type-badge { background: var(--text-secondary); opacity: 0.8; }
  }
  .detail-sci {
    font-size: 14px; color: var(--text-secondary); font-style: italic; margin: 4px 0;
    display: flex; align-items: center; gap: 4px;
  }
  .detail-taxonomy { font-size: 13px; color: var(--text-secondary); margin: 0 0 10px; }
  .detail-intro {
    font-size: 14px; color: var(--text-primary); line-height: 1.6;
    margin: 0 0 20px; padding-bottom: 16px;
    border-bottom: 1px solid var(--border-color);
  }

  .detail-sections {
    display: flex; flex-direction: column; gap: 16px;
    .detail-section {
      display: flex; gap: 14px;
      .section-icon {
        width: 36px; height: 36px; border-radius: 10px; flex-shrink: 0;
        display: flex; align-items: center; justify-content: center;
        color: #fff; font-size: 16px;
      }
      .section-content {
        flex: 1; min-width: 0;
        h4 { font-size: 13px; font-weight: 600; color: var(--text-primary); margin: 0 0 4px; }
        p { font-size: 13px; color: var(--text-secondary); line-height: 1.6; margin: 0; word-break: break-word; }
      }
    }
  }
}

@media (max-width: 900px) {
  .pest-guide-page .pest-grid { grid-template-columns: repeat(2, 1fr); }
  .pest-guide-page .filter-panel { grid-template-columns: 1fr; }
}
@media (max-width: 560px) {
  .pest-guide-page .pest-grid { grid-template-columns: 1fr; }
}
</style>
