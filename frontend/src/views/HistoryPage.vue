<template>
  <div class="history-page">
    <div class="page-header">
      <h1 class="page-title">检测历史记录</h1>
      <p class="page-subtitle">查看和管理您的所有检测记录</p>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索文件名..."
        size="default"
        class="search-input"
        clearable
        @clear="handleSearch"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
        <template #append>
          <el-button @click="handleSearch">搜索</el-button>
        </template>
      </el-input>

      <el-select v-model="filterStatus" placeholder="状态筛选" size="default" class="filter-select" @change="handleSearch" clearable>
        <el-option label="全部" value="" />
        <el-option label="检测完成" value="completed" />
        <el-option label="检测中" value="processing" />
        <el-option label="失败" value="failed" />
      </el-select>
    </div>

    <div class="toolbar" v-if="historyRecords.length > 0">
      <el-checkbox
        v-model="allChecked"
        :indeterminate="isIndeterminate"
        @change="handleCheckAll"
      >
        全选
      </el-checkbox>
      <span class="toolbar-count" v-if="selectedIds.length > 0">已选 {{ selectedIds.length }} 条</span>
      <el-button
        v-if="selectedIds.length > 0"
        type="danger"
        size="small"
        @click="handleBatchDelete"
      >
        <el-icon><Delete /></el-icon>
        批量删除
      </el-button>
    </div>

    <div class="history-list" v-loading="loading">
      <div
        v-for="record in historyRecords"
        :key="record.id"
        class="history-card"
        :class="{ selected: selectedIds.includes(record.id) }"
      >
        <el-checkbox
          v-model="record._checked"
          class="card-checkbox"
          @change="handleRecordCheck"
        />

        <div class="record-preview">
          <img v-if="record.media_type === 'video'" :src="record.result_image" alt="视频检测" class="preview-image" />
          <img v-else-if="record.result_image" :src="record.result_image" alt="检测结果" class="preview-image" />
          <div v-else class="preview-placeholder">
            <el-icon :size="24" color="#9ca3af"><Picture /></el-icon>
          </div>
          <div v-if="record.media_type === 'video'" class="video-badge">
            <el-icon><VideoCamera /></el-icon>
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
            <span v-if="record.media_type === 'video'" class="meta-item video-meta">
              <el-icon><VideoCamera /></el-icon>
              视频 {{ record.duration }}s / {{ record.frame_count }}帧
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
          <el-button size="small" @click="viewDetail(record)">查看</el-button>
          <el-button size="small" type="danger" @click="deleteRecord(record)">删除</el-button>
        </div>
      </div>
    </div>

    <div v-if="!loading && historyRecords.length === 0" class="empty-state">
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

    <!-- 检测结果详情弹窗 -->
    <el-dialog v-model="detailVisible" title="检测详情" width="720px" destroy-on-close>
      <div v-if="detailRecord" class="detail-content">
        <template v-if="detailRecord.media_type === 'video'">
          <video :src="detailRecord.result_video_url" controls class="detail-video" />
          <div class="detail-meta">
            <div class="detail-meta-item">
              <span class="detail-meta-label">文件名</span>
              <span class="detail-meta-value">{{ detailRecord.filename }}</span>
            </div>
            <div class="detail-meta-item">
              <span class="detail-meta-label">模型</span>
              <span class="detail-meta-value">{{ detailRecord.model_name }}</span>
            </div>
            <div class="detail-meta-item">
              <span class="detail-meta-label">视频时长</span>
              <span class="detail-meta-value">{{ detailRecord.duration }}s ({{ detailRecord.frame_count }}帧)</span>
            </div>
            <div class="detail-meta-item">
              <span class="detail-meta-label">检测目标</span>
              <span class="detail-meta-value">{{ detailRecord.total_objects }} 个</span>
            </div>
            <div class="detail-meta-item">
              <span class="detail-meta-label">耗时</span>
              <span class="detail-meta-value">{{ detailRecord.detection_time }}s</span>
            </div>
          </div>
        </template>
        <template v-else>
          <div class="detail-images">
            <div class="detail-image-block">
              <span class="detail-image-label">原图</span>
              <img :src="detailRecord.original_image" class="detail-image" />
            </div>
            <div class="detail-image-block">
              <span class="detail-image-label">检测结果</span>
              <img :src="detailRecord.result_image" class="detail-image" />
            </div>
          </div>
          <div class="detail-meta">
            <div class="detail-meta-item">
              <span class="detail-meta-label">文件名</span>
              <span class="detail-meta-value">{{ detailRecord.filename }}</span>
            </div>
            <div class="detail-meta-item">
              <span class="detail-meta-label">模型</span>
              <span class="detail-meta-value">{{ detailRecord.model_name }}</span>
            </div>
            <div class="detail-meta-item">
              <span class="detail-meta-label">检测目标</span>
              <span class="detail-meta-value">{{ detailRecord.total_objects }} 个</span>
            </div>
            <div class="detail-meta-item">
              <span class="detail-meta-label">耗时</span>
              <span class="detail-meta-value">{{ detailRecord.detection_time }}s</span>
            </div>
          </div>
          <div v-if="detailRecord.boxes && detailRecord.boxes.length > 0" class="detail-boxes">
            <h4 class="detail-boxes-title">检测框列表</h4>
            <el-table :data="detailRecord.boxes" size="small" stripe max-height="240">
              <el-table-column type="index" label="#" width="40" />
              <el-table-column prop="class_name" label="类别" min-width="100" />
              <el-table-column label="置信度" min-width="100">
                <template #default="{ row }">
                  <span :style="{ color: row.confidence >= 0.8 ? '#059669' : row.confidence >= 0.5 ? '#d97706' : '#dc2626' }">
                    {{ (row.confidence * 100).toFixed(1) }}%
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="位置 (x1,y1)-(x2,y2)" min-width="160">
                <template #default="{ row }">
                  ({{ Math.round(row.x1) }},{{ Math.round(row.y1) }})-({{ Math.round(row.x2) }},{{ Math.round(row.y2) }})
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Search, Clock, Picture, Aim, Help, Plus, VideoCamera, Delete,
} from "@element-plus/icons-vue";
import { getHistoryList, getHistoryDetail, deleteHistory, batchDeleteHistory } from "../api/history";

const searchQuery = ref("");
const filterStatus = ref("");
const loading = ref(false);
const historyRecords = ref([]);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);

const detailVisible = ref(false);
const detailRecord = ref(null);

// 批量选择
const selectedIds = computed(() =>
  historyRecords.value.filter(r => r._checked).map(r => r.id)
);
const allChecked = computed(() =>
  historyRecords.value.length > 0 && selectedIds.value.length === historyRecords.value.length
);
const isIndeterminate = computed(() =>
  selectedIds.value.length > 0 && selectedIds.value.length < historyRecords.value.length
);

const handleCheckAll = (val) => {
  historyRecords.value.forEach(r => { r._checked = val; });
};

const handleRecordCheck = () => {
  // computed 自动更新
};

const fetchHistory = async () => {
  loading.value = true;
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
    };
    if (searchQuery.value) params.keyword = searchQuery.value;
    if (filterStatus.value) params.status = filterStatus.value;
    const res = await getHistoryList(params);
    if (res.success) {
      historyRecords.value = res.data.map(r => ({ ...r, _checked: false }));
      total.value = res.total;
    }
  } catch (error) {
    console.error("获取历史记录失败:", error);
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  currentPage.value = 1;
  fetchHistory();
};

onMounted(() => { fetchHistory(); });

const getStatusText = (status) => {
  const texts = { completed: "检测完成", processing: "检测中", failed: "失败" };
  return texts[status] || status;
};

const viewDetail = async (record) => {
  try {
    const res = await getHistoryDetail(record.id);
    detailRecord.value = res;
    detailVisible.value = true;
  } catch (e) {
    ElMessage.error("获取详情失败");
  }
};

const deleteRecord = async (record) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除记录 "${record.filename}" 吗？`,
      "确认删除",
      { confirmButtonText: "删除", cancelButtonText: "取消", type: "warning" }
    );
    const res = await deleteHistory(record.id);
    if (res.success) {
      ElMessage.success("删除成功");
      fetchHistory();
    }
  } catch (error) {
    if (error !== "cancel") {
      console.error("删除失败:", error);
    }
  }
};

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedIds.value.length} 条记录吗？此操作不可恢复。`,
      "批量删除",
      { confirmButtonText: "删除", cancelButtonText: "取消", type: "warning" }
    );
    const res = await batchDeleteHistory(selectedIds.value);
    if (res.success) {
      ElMessage.success(res.message);
      fetchHistory();
    }
  } catch (error) {
    if (error !== "cancel") {
      console.error("批量删除失败:", error);
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
  width: 100%; max-width: 1040px; margin: 0 auto;

  .page-header {
    margin-bottom: 24px;
    animation: fade-up 0.6s var(--ease-out-expo) both;
    .page-title { font-size: 24px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; }
    .page-subtitle { font-size: 14px; color: var(--text-secondary); }
  }

  .search-bar {
    display: flex; gap: 16px; margin-bottom: 16px; align-items: center;
    animation: fade-up 0.6s var(--ease-out-expo) both; animation-delay: 0.1s;
    .search-input { flex: 1; max-width: 360px; }
    .filter-select { width: 140px; }
  }

  .toolbar {
    display: flex; align-items: center; gap: 12px; margin-bottom: 16px; padding: 10px 16px;
    background: #ffffff; border-radius: 10px; box-shadow: var(--card-shadow); border: 1px solid var(--border-color);
    animation: fade-up 0.6s var(--ease-out-expo) both; animation-delay: 0.12s;
    .toolbar-count { font-size: 13px; color: var(--text-secondary); }
  }

  .history-list { display: flex; flex-direction: column; gap: 16px; }

  .history-card {
    background-color: #ffffff; border-radius: 12px; padding: 20px;
    box-shadow: var(--card-shadow); display: flex; align-items: center; gap: 16px;
    transition: box-shadow 0.3s var(--ease-out-expo), transform 0.3s var(--ease-out-expo), border-color 0.2s ease;
    border: 2px solid transparent;
    animation: fade-up 0.6s var(--ease-out-expo) both;
    &:nth-child(1) { animation-delay: 0.15s; }
    &:nth-child(2) { animation-delay: 0.25s; }
    &:nth-child(3) { animation-delay: 0.35s; }
    &:nth-child(4) { animation-delay: 0.45s; }
    &:nth-child(5) { animation-delay: 0.55s; }
    &:hover { box-shadow: var(--card-shadow-hover); transform: translateY(-2px); }
    &.selected { border-color: var(--primary-color); background-color: rgba(180, 83, 9, 0.02); }

    .card-checkbox { flex-shrink: 0; }

    .record-preview {
      position: relative; width: 120px; height: 80px; border-radius: 8px; overflow: hidden;
      background-color: #f3f4f6; display: flex; align-items: center; justify-content: center;
      .video-badge {
        position: absolute; top: 6px; right: 6px; width: 24px; height: 24px;
        background: rgba(0,0,0,0.6); border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        .el-icon { font-size: 12px; color: #fff; }
      }
      .status-badge {
        position: absolute; bottom: 8px; left: 8px; padding: 4px 10px;
        border-radius: 12px; font-size: 12px; color: white;
        &.completed { background-color: rgba(180, 83, 9, 0.9); }
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
        .detected-tag { padding: 3px 8px; background-color: rgba(180, 83, 9, 0.1); color: #b45309; border-radius: 4px; font-size: 12px; }
      }
    }

    .record-actions { display: flex; gap: 8px; }
  }

  .empty-state {
    display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 0;
    animation: fade-up 0.6s var(--ease-out-expo) both; animation-delay: 0.2s;
    .empty-icon { color: #9ca3af; margin-bottom: 16px; animation: pulse-glow 2.5s ease-in-out infinite; }
    .empty-text { font-size: 15px; color: var(--text-secondary); margin-bottom: 24px; }
  }

  .pagination { display: flex; justify-content: center; margin-top: 24px; }
}

.preview-image { width: 100%; height: 100%; object-fit: cover; }
.detected-tag.more { background-color: rgba(107, 114, 128, 0.1); color: #6b7280; }

.detail-content { display: flex; flex-direction: column; gap: 20px; }
.detail-images { display: flex; gap: 16px; }
.detail-image-block { flex: 1; }
.detail-image-label { display: block; font-size: 13px; color: var(--text-secondary); margin-bottom: 8px; }
.detail-image { width: 100%; border-radius: 8px; object-fit: contain; max-height: 280px; background: #f3f4f6; }

.detail-meta {
  display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
  .detail-meta-item { display: flex; flex-direction: column; }
  .detail-meta-label { font-size: 12px; color: var(--text-secondary); margin-bottom: 2px; }
  .detail-meta-value { font-size: 14px; font-weight: 500; color: var(--text-primary); }
}

.detail-boxes-title { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; }
.detail-video { width: 100%; border-radius: 8px; max-height: 400px; background: #000; }
.video-meta { color: var(--primary-color) !important; font-weight: 500; }
</style>
