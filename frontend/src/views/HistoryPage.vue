<template>
  <div class="history-page">
    <div class="page-header">
      <h1 class="page-title">检测历史记录</h1>
      <p class="page-subtitle">查看和管理您的所有检测记录</p>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索检测记录..."
        size="default"
        class="search-input"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-select v-model="filterStatus" placeholder="状态筛选" size="default" class="filter-select">
        <el-option label="全部" value="" />
        <el-option label="检测完成" value="completed" />
        <el-option label="检测中" value="processing" />
        <el-option label="失败" value="failed" />
      </el-select>
    </div>

    <div class="history-list" v-loading="loading">
      <div
        v-for="record in filteredRecords"
        :key="record.id"
        class="history-card"
      >
        <div class="record-preview">
          <img v-if="record.result_image" :src="record.result_image" alt="检测结果" class="preview-image" />
          <div v-else class="preview-placeholder">
            <el-icon :size="24" color="#9ca3af"><Picture /></el-icon>
          </div>
          <div class="status-badge" :class="record.status">
            {{ getStatusText(record.status) }}
          </div>
        </div>

        <div class="record-info">
          <div class="record-header">
            <span class="record-filename">{{ record.filename }}</span>
            <span class="record-type">{{ record.model_name }}</span>
          </div>
          <div class="record-meta">
            <span class="meta-item">
              <el-icon><Clock /></el-icon>
              {{ record.created_at }}
            </span>
            <span class="meta-item">
              <el-icon><Aim /></el-icon>
              {{ record.total_objects }} 个目标
            </span>
            <span class="meta-item">
              耗时 {{ record.detection_time }}s
            </span>
          </div>
          <div class="record-tags" v-if="record.boxes && record.boxes.length > 0">
            <span v-for="box in record.boxes.slice(0, 5)" :key="box.class_name" class="detected-tag">
              {{ box.class_name }}
            </span>
            <span v-if="record.boxes.length > 5" class="detected-tag more">
              +{{ record.boxes.length - 5 }}
            </span>
          </div>
        </div>

        <div class="record-actions">
          <el-button size="small">查看</el-button>
          <el-button size="small" type="danger" @click="deleteRecord(record)">删除</el-button>
        </div>
      </div>
    </div>

    <div v-if="!loading && filteredRecords.length === 0" class="empty-state">
      <el-icon :size="64" class="empty-icon"><Help /></el-icon>
      <p class="empty-text">暂无检测记录</p>
      <el-button type="primary" @click="$router.push('/detection')">
        <el-icon><Plus /></el-icon>
        开始检测
      </el-button>
    </div>

    <div v-if="total > pageSize" class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import {
  Search, Clock, Picture, Aim, Help, Plus,
} from "@element-plus/icons-vue";
import { getHistoryList, deleteHistory } from "../api/history";

const searchQuery = ref("");
const filterStatus = ref("");
const loading = ref(false);
const historyRecords = ref([]);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);

const fetchHistory = async () => {
  loading.value = true;
  try {
    const res = await getHistoryList({
      page: currentPage.value,
      page_size: pageSize.value,
    });
    if (res.success) {
      historyRecords.value = res.data;
      total.value = res.total;
    }
  } catch (error) {
    console.error("获取历史记录失败:", error);
  } finally {
    loading.value = false;
  }
};

onMounted(() => { fetchHistory(); });

const filteredRecords = computed(() => {
  return historyRecords.value.filter((record) => {
    const matchesSearch = !searchQuery.value || record.filename.toLowerCase().includes(searchQuery.value.toLowerCase());
    const matchesStatus = !filterStatus.value || record.status === filterStatus.value;
    return matchesSearch && matchesStatus;
  });
});

const getStatusText = (status) => {
  const texts = { completed: "检测完成", processing: "检测中", failed: "失败" };
  return texts[status] || status;
};

const deleteRecord = async (record) => {
  if (confirm(`确定要删除记录 "${record.filename}" 吗？`)) {
    try {
      const res = await deleteHistory(record.id);
      if (res.success) {
        ElMessage.success("删除成功");
        fetchHistory();
      }
    } catch (error) {
      console.error("删除失败:", error);
    }
  }
};

const handlePageChange = (page) => {
  currentPage.value = page;
  fetchHistory();
};
</script>

<style scoped lang="scss">
.history-page {
  width: 100%;

  .page-header {
    margin-bottom: 24px;
    .page-title { font-size: 24px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; }
    .page-subtitle { font-size: 14px; color: var(--text-secondary); }
  }

  .search-bar {
    display: flex; gap: 16px; margin-bottom: 24px; align-items: center;
    .search-input { flex: 1; max-width: 300px; }
    .filter-select { width: 140px; }
  }

  .history-list { display: flex; flex-direction: column; gap: 16px; }

  .history-card {
    background-color: #ffffff; border-radius: 12px; padding: 20px;
    box-shadow: var(--card-shadow); display: flex; align-items: center; gap: 20px;
    transition: all 0.2s;
    &:hover { box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08); transform: translateY(-2px); }

    .record-preview {
      position: relative; width: 120px; height: 80px; border-radius: 8px; overflow: hidden;
      background-color: #f3f4f6; display: flex; align-items: center; justify-content: center;
      .status-badge {
        position: absolute; bottom: 8px; left: 8px; padding: 4px 10px;
        border-radius: 12px; font-size: 12px; color: white;
        &.completed { background-color: rgba(13, 148, 136, 0.9); }
        &.processing { background-color: rgba(59, 130, 246, 0.9); }
        &.failed { background-color: rgba(239, 68, 68, 0.9); }
      }
    }

    .record-info {
      flex: 1; min-width: 0;
      .record-header { display: flex; align-items: center; gap: 12px; margin-bottom: 10px;
        .record-filename { font-size: 15px; font-weight: 500; color: var(--text-primary); }
        .record-type { padding: 3px 8px; background-color: #f3f4f6; border-radius: 4px; font-size: 12px; color: var(--text-secondary); }
      }
      .record-meta { display: flex; gap: 20px; margin-bottom: 10px;
        .meta-item { display: flex; align-items: center; gap: 4px; font-size: 13px; color: var(--text-secondary); }
      }
      .record-tags { display: flex; flex-wrap: wrap; gap: 6px;
        .detected-tag { padding: 3px 8px; background-color: rgba(13, 148, 136, 0.1); color: #0d9488; border-radius: 4px; font-size: 12px; }
      }
    }

    .record-actions { display: flex; gap: 8px; }
  }

  .empty-state {
    display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 0;
    .empty-icon { color: #9ca3af; margin-bottom: 16px; }
    .empty-text { font-size: 15px; color: var(--text-secondary); margin-bottom: 24px; }
  }

  .pagination { display: flex; justify-content: center; margin-top: 24px; }
}

.preview-image { width: 100%; height: 100%; object-fit: cover; }

.detected-tag.more { background-color: rgba(107, 114, 128, 0.1); color: #6b7280; }
</style>
