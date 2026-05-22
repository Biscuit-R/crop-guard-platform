<template>
  <div class="header-container">
    <div class="breadcrumbs">
      <el-icon class="breadcrumb-icon"><House /></el-icon>
      <span class="breadcrumb-separator">/</span>
      <span class="breadcrumb-text">{{ currentRouteName }}</span>
    </div>

    <div class="header-actions">
      <el-dropdown trigger="click" @command="handleCommand">
        <div class="user-dropdown">
          <el-avatar class="user-avatar" size="32">
            {{ (userStore.userInfo?.username || 'U')[0].toUpperCase() }}
          </el-avatar>
          <div class="user-info">
            <div class="user-name">{{ userStore.userInfo?.username || '用户' }}</div>
            <div class="user-role">{{ userStore.userInfo?.role === 'admin' ? '管理员' : '普通用户' }}</div>
          </div>
          <el-icon class="dropdown-icon"><CaretBottom /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <el-icon><User /></el-icon>个人中心
            </el-dropdown-item>
            <el-dropdown-item command="password">
              <el-icon><Lock /></el-icon>修改密码
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <el-icon><SwitchButton /></el-icon>退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="passwordDialogVisible" title="修改密码" width="400px" :close-on-click-modal="false">
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="80px">
        <el-form-item label="当前密码" prop="current_password">
          <el-input v-model="pwdForm.current_password" type="password" show-password placeholder="请输入当前密码" />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="请输入新密码" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="pwdForm.confirm_password" type="password" show-password placeholder="请确认新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="pwdLoading" @click="handleChangePassword">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { CaretBottom, House, User, Lock, SwitchButton } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useUserStore } from "../stores/user";

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const currentRouteName = computed(() => route.meta?.title || "数据看板");

onMounted(async () => {
  if (userStore.isLoggedIn && !userStore.userInfo) {
    try {
      await userStore.fetchUserInfo();
    } catch (error) {
      console.error("获取用户信息失败:", error);
    }
  }
});

async function handleCommand(command) {
  if (command === "profile") {
    router.push("/profile");
  } else if (command === "password") {
    passwordDialogVisible.value = true;
  } else if (command === "logout") {
    try {
      await ElMessageBox.confirm("确定要退出登录吗？", "提示", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      });
      await userStore.logout();
      router.push("/login");
    } catch {
      // 用户取消
    }
  }
}

// 修改密码
const passwordDialogVisible = ref(false);
const pwdLoading = ref(false);
const pwdFormRef = ref(null);
const pwdForm = reactive({
  current_password: "",
  new_password: "",
  confirm_password: "",
});
const pwdRules = {
  current_password: [
    { required: true, message: "请输入当前密码", trigger: "blur" },
  ],
  new_password: [
    { required: true, message: "请输入新密码", trigger: "blur" },
    { min: 6, max: 30, message: "密码长度在6到30个字符", trigger: "blur" },
  ],
  confirm_password: [
    { required: true, message: "请确认新密码", trigger: "blur" },
    {
      validator: (rule, value, callback) => {
        if (value !== pwdForm.new_password) {
          callback(new Error("两次输入的密码不一致"));
        } else {
          callback();
        }
      },
      trigger: "blur",
    },
  ],
};

async function handleChangePassword() {
  try {
    await pwdFormRef.value.validate();
  } catch {
    return;
  }
  pwdLoading.value = true;
  try {
    const res = await userStore.changePassword({
      current_password: pwdForm.current_password,
      new_password: pwdForm.new_password,
    });
    if (res.success) {
      ElMessage.success("密码修改成功，请重新登录");
      passwordDialogVisible.value = false;
      pwdForm.current_password = "";
      pwdForm.new_password = "";
      pwdForm.confirm_password = "";
      await userStore.logout();
      router.push("/login");
    }
  } catch {
    // 错误已在 axios 拦截器中处理
  } finally {
    pwdLoading.value = false;
  }
}
</script>

<style scoped>
.header-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.breadcrumbs {
  display: flex;
  align-items: center;
}

.breadcrumb-icon {
  font-size: 14px;
  color: var(--text-secondary);
}

.breadcrumb-separator {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 8px;
}

.breadcrumb-text {
  font-size: 14px;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  align-items: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-md);
  transition: background-color 0.2s ease;
}

.user-dropdown:hover {
  background-color: var(--primary-light);
}

.user-avatar {
  margin-right: 8px;
}

.user-info {
  margin-right: 6px;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.user-role {
  font-size: 12px;
  color: var(--text-secondary);
}

.dropdown-icon {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
