<template>
  <div class="pest-guide-page">
    <div class="page-header">
      <h1 class="page-title">病虫害图鉴</h1>
      <p class="page-subtitle">平台支持检测的所有病虫害类别</p>
    </div>

    <div class="search-container">
      <el-input v-model="searchQuery" placeholder="搜索病虫害类别..." size="default" class="search-input">
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon pest-icon"><el-icon><Aim /></el-icon></div>
        <div class="stat-info">
          <div class="stat-value">{{ totalPests }}</div>
          <div class="stat-label">病虫害总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon category-icon"><el-icon><Grid /></el-icon></div>
        <div class="stat-info">
          <div class="stat-value">{{ categories.length }}</div>
          <div class="stat-label">分类数量</div>
        </div>
      </div>
    </div>

    <div class="pest-categories">
      <div v-for="category in filteredCategories" :key="category.id" class="category-card">
        <div class="category-header">
          <div class="category-icon" :style="{ backgroundColor: category.color }">
            <el-icon :size="24" color="white"><component :is="category.icon" /></el-icon>
          </div>
          <div class="category-info">
            <div class="category-name">{{ category.name }}</div>
            <div class="category-count">{{ category.pests.length }} 种</div>
          </div>
        </div>
        <div class="pest-list">
          <div v-for="pest in category.pests" :key="pest.id" class="pest-item">
            <el-icon :size="14" class="pest-item-icon"><CircleCheck /></el-icon>
            <div class="pest-detail">
              <span class="pest-name">{{ pest.name }}</span>
              <span class="pest-desc">{{ pest.description }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="filteredCategories.length === 0" class="empty-state">
      <el-icon :size="64" class="empty-icon"><Help /></el-icon>
      <p class="empty-text">未找到匹配的病虫害类别</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import {
  Search, Aim, Grid, CircleCheck, Help,
  Sunny, Warning, FirstAidKit, Opportunity,
} from "@element-plus/icons-vue";
import { getPestList } from "../api/detection";

const searchQuery = ref("");
const loading = ref(false);
const categories = ref([]);

const categoryConfig = {
  "真菌病害": { icon: Warning, color: "#f59e0b" },
  "细菌病害": { icon: FirstAidKit, color: "#ef4444" },
  "病毒病害": { icon: Opportunity, color: "#8b5cf6" },
  "虫害": { icon: Sunny, color: "#0d9488" },
};

const fetchPests = async () => {
  loading.value = true;
  try {
    const res = await getPestList();
    if (res.success) {
      const grouped = {};
      for (const pest of res.data) {
        if (!grouped[pest.category]) {
          grouped[pest.category] = [];
        }
        grouped[pest.category].push({
          id: pest.id,
          name: pest.chinese_name,
          description: pest.description,
        });
      }
      categories.value = Object.entries(grouped).map(([name, pests], index) => ({
        id: index + 1,
        name,
        pests,
        icon: categoryConfig[name]?.icon || Warning,
        color: categoryConfig[name]?.color || "#6b7280",
      }));
    }
  } catch (e) {
    console.error("获取病虫害列表失败:", e);
  } finally {
    loading.value = false;
  }
};

const filteredCategories = computed(() => {
  if (!searchQuery.value) return categories.value;
  const query = searchQuery.value.toLowerCase();
  return categories.value.map((category) => ({
    ...category,
    pests: category.pests.filter(
      (pest) => pest.name.toLowerCase().includes(query) || pest.description.toLowerCase().includes(query)
    ),
  })).filter((category) => category.name.toLowerCase().includes(query) || category.pests.length > 0);
});

const totalPests = computed(() => categories.value.reduce((sum, c) => sum + c.pests.length, 0));

onMounted(fetchPests);
</script>

<style scoped lang="scss">
.pest-guide-page {
  width: 100%; max-width: 1040px; margin: 0 auto;

  .page-header {
    margin-bottom: 24px;
    animation: fade-up 0.6s var(--ease-out-expo) both;
    .page-title { font-size: 24px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; }
    .page-subtitle { font-size: 14px; color: var(--text-secondary); }
  }

  .search-container { margin-bottom: 24px; animation: fade-up 0.6s var(--ease-out-expo) both; animation-delay: 0.1s; .search-input { max-width: 300px; } }

  .stats-cards {
    display: flex; gap: 20px; margin-bottom: 24px;
    .stat-card {
      flex: 1; max-width: 200px; background-color: #ffffff; border-radius: 12px;
      padding: 20px; box-shadow: var(--card-shadow); display: flex; align-items: center; gap: 16px;
      transition: box-shadow 0.3s var(--ease-out-expo), transform 0.3s var(--ease-out-expo);
      animation: fade-up 0.6s var(--ease-out-expo) both;
      &:nth-child(1) { animation-delay: 0.15s; }
      &:nth-child(2) { animation-delay: 0.25s; }
      &:hover { box-shadow: var(--card-shadow-hover); transform: translateY(-2px); }
      &:active { transform: scale(0.98); box-shadow: var(--card-shadow-active); }
      .stat-icon {
        width: 50px; height: 50px; border-radius: 12px; display: flex;
        align-items: center; justify-content: center; color: white; font-size: 24px;
        &.pest-icon { background: #0d9488; }
        &.category-icon { background: #3b82f6; }
      }
      .stat-info {
        .stat-value { font-size: 24px; font-weight: 600; color: var(--text-primary); }
        .stat-label { font-size: 13px; color: var(--text-secondary); }
      }
    }
  }

  .pest-categories {
    display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px;
    .category-card {
      background-color: #ffffff; border-radius: 12px; padding: 20px;
      box-shadow: var(--card-shadow);
      transition: box-shadow 0.3s var(--ease-out-expo), transform 0.3s var(--ease-out-expo);
      animation: fade-up 0.6s var(--ease-out-expo) both;
      &:nth-child(1) { animation-delay: 0.3s; }
      &:nth-child(2) { animation-delay: 0.4s; }
      &:nth-child(3) { animation-delay: 0.5s; }
      &:nth-child(4) { animation-delay: 0.6s; }
      &:hover { box-shadow: var(--card-shadow-hover); transform: translateY(-2px); }

      .category-header {
        display: flex; align-items: center; margin-bottom: 16px;
        .category-icon {
          width: 50px; height: 50px; border-radius: 12px; display: flex;
          align-items: center; justify-content: center; margin-right: 16px;
          transition: transform 0.3s var(--ease-spring);
        }
        &:hover .category-icon { transform: scale(1.05) rotate(-5deg); }
        .category-info {
          .category-name { font-size: 18px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
          .category-count { font-size: 13px; color: var(--text-secondary); }
        }
      }

      .pest-list {
        display: flex; flex-direction: column; gap: 10px;
        .pest-item {
          display: flex; align-items: flex-start; gap: 8px; padding: 10px 14px;
          background-color: #f0fdfa; border-radius: 8px; cursor: pointer;
          transition: background-color 0.2s ease, transform 0.2s var(--ease-out-expo);
          animation: fade-in 0.6s var(--ease-out-expo) both;
          &:nth-child(1) { animation-delay: 0.4s; }
          &:nth-child(2) { animation-delay: 0.5s; }
          &:nth-child(3) { animation-delay: 0.6s; }
          &:nth-child(4) { animation-delay: 0.7s; }
          &:nth-child(5) { animation-delay: 0.8s; }
          &:hover { background-color: #ccfbf1; transform: translateX(4px); }
          .pest-item-icon { color: #0d9488; margin-top: 2px; flex-shrink: 0; transition: transform 0.3s var(--ease-spring); }
          &:hover .pest-item-icon { transform: scale(1.2); }
          .pest-detail {
            display: flex; flex-direction: column;
            .pest-name { font-size: 14px; font-weight: 500; color: var(--text-primary); }
            .pest-desc { font-size: 12px; color: var(--text-secondary); margin-top: 2px; line-height: 1.4; }
          }
        }
      }
    }
  }

  .empty-state {
    display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 0;
    animation: fade-up 0.6s var(--ease-out-expo) both; animation-delay: 0.3s;
    .empty-icon { color: #9ca3af; margin-bottom: 16px; animation: pulse-glow 2.5s ease-in-out infinite; }
    .empty-text { font-size: 15px; color: var(--text-secondary); }
  }
}
</style>
