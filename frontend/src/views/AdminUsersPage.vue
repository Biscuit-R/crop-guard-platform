<template>
  <div class="admin-page">
    <div class="page-header">
      <h1 class="page-title">用户管理</h1>
      <p class="page-subtitle">管理系统用户、角色和状态</p>
    </div>

    <div class="section-card">
      <el-table :data="users" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'warning'" size="small">
              {{ row.is_active ? '正常' : '已禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="注册时间" min-width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-select
              v-model="row.role"
              size="small"
              style="width: 90px; margin-right: 8px"
              @change="handleRoleChange(row)"
              :disabled="row.id === currentUserId"
            >
              <el-option label="管理员" value="admin" />
              <el-option label="普通用户" value="user" />
            </el-select>
            <el-button
              size="small"
              :type="row.is_active ? 'warning' : 'success'"
              @click="handleToggleStatus(row)"
              :disabled="row.id === currentUserId"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(row)"
              :disabled="row.id === currentUserId"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useUserStore } from "../stores/user";

const userStore = useUserStore();
const users = ref([]);
const currentUserId = computed(() => userStore.userInfo?.id);

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

async function loadUsers() {
  try {
    const res = await userStore.fetchUsers();
    if (res.success) {
      users.value = res.data.users;
    }
  } catch (e) {
    console.error("获取用户列表失败:", e);
  }
}

async function handleRoleChange(row) {
  try {
    const res = await userStore.updateUserRole(row.id, row.role);
    if (res.success) {
      ElMessage.success("角色已更新");
    } else {
      ElMessage.error(res.message || "更新失败");
      loadUsers();
    }
  } catch {
    loadUsers();
  }
}

async function handleToggleStatus(row) {
  const newStatus = !row.is_active;
  const text = newStatus ? "启用" : "禁用";
  try {
    await ElMessageBox.confirm(`确定要${text}用户 "${row.username}" 吗？`, "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    const res = await userStore.updateUserStatus(row.id, newStatus);
    if (res.success) {
      ElMessage.success(res.message);
      row.is_active = newStatus;
    }
  } catch {
    // 用户取消
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除用户 "${row.username}" 吗？此操作不可恢复。`, "警告", {
      confirmButtonText: "确定删除",
      cancelButtonText: "取消",
      type: "error",
    });
    const res = await userStore.deleteUser(row.id);
    if (res.success) {
      ElMessage.success("用户已删除");
      users.value = users.value.filter(u => u.id !== row.id);
    }
  } catch {
    // 用户取消
  }
}

onMounted(loadUsers);
</script>

<style scoped lang="scss">
.admin-page {
  width: 100%; max-width: 1040px; margin: 0 auto;

  .page-header {
    margin-bottom: 24px;
    .page-title { font-size: 24px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; }
    .page-subtitle { font-size: 14px; color: var(--text-secondary); }
  }

  .section-card {
    background-color: var(--surface); border-radius: var(--radius-lg); padding: 20px;
    box-shadow: var(--card-shadow); animation: fade-up 0.5s var(--ease-out-expo) both;
  }
}
</style>
