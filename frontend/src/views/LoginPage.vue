<template>
  <div class="login-container">
    <div class="login-card">
      <div class="card-top">
        <div class="login-header">
          <div class="logo-icon">
            <svg viewBox="0 0 32 32" width="38" height="38" fill="none">
              <path d="M16 3C10 3 5 8 5 14c0 4 2 7.5 5 10v2c0 .6.4 1 1 1h10c.6 0 1-.4 1-1v-2c3-2.5 5-6 5-10 0-6-5-11-11-11z" fill="rgba(255,255,255,0.15)" stroke="#ffffff" stroke-width="1.5"/>
              <path d="M16 10c-1.5-3-4-4-5.5-2.5 2.5 0 4.2-.8 5.5-.5" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round" fill="none"/>
              <path d="M16 10c1.5-3 4-4 5.5-2.5-2.5 0-4.2-.8-5.5-.5" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round" fill="none"/>
              <path d="M16 14c-2-2.5-4.5-2.5-5.5-1 2 0 3.8-.5 5.5-.5" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round" fill="none"/>
              <path d="M16 14c2-2.5 4.5-2.5 5.5-1-2 0-3.8-.5-5.5-.5" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round" fill="none"/>
              <path d="M16 18v4" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="logo-text">
            <h1 class="login-title">Crop Guard</h1>
            <p class="login-subtitle">农作物病虫害智能检测平台</p>
          </div>
        </div>
      </div>

      <div class="card-middle">
        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          class="login-form"
        >
          <div class="input-group">
            <label class="input-label">用户名</label>
            <el-form-item prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="请输入用户名"
                size="large"
                @keyup.enter="handleLogin"
              >
                <template #prefix>
                  <el-icon><User /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </div>

          <div class="input-group">
            <label class="input-label">密码</label>
            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                @keyup.enter="handleLogin"
              >
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </div>

          <el-form-item class="form-actions">
            <el-checkbox v-model="loginForm.remember">记住我</el-checkbox>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" size="large" class="login-btn" :loading="loading" @click="handleLogin">
              登录
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <div class="card-bottom">
        <div class="register-link">
          <span>还没有账号？</span>
          <router-link to="/register">立即注册</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { User, Lock } from "@element-plus/icons-vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { useUserStore } from "../stores/user";

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

const loginForm = reactive({
  username: "",
  password: "",
  remember: false,
});

const loginRules = {
  username: [
    { required: true, message: "请输入用户名", trigger: "blur" },
    { min: 3, max: 20, message: "用户名长度在3到20个字符", trigger: "blur" },
  ],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, max: 30, message: "密码长度在6到30个字符", trigger: "blur" },
  ],
};

const loginFormRef = ref(null);
const loading = ref(false);

const handleLogin = () => {
  loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        const res = await userStore.login({
          username: loginForm.username,
          password: loginForm.password,
          remember: loginForm.remember,
        });
        if (res.success) {
          ElMessage.success("登录成功");
          const redirect = route.query.redirect;
          router.push(redirect || "/dashboard");
        }
      } catch (error) {
        // 错误已在 axios 拦截器中处理
      } finally {
        loading.value = false;
      }
    }
  });
};
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: url('/login-bg.jpg') center/cover no-repeat;
  padding: 40px;
}

.login-card {
  width: 100%;
  max-width: 360px;
  border-radius: 16px;
  overflow: hidden;
  box-shadow:
    0 24px 80px rgba(0, 0, 0, 0.28),
    0 12px 32px rgba(0, 0, 0, 0.15),
    0 4px 12px rgba(0, 0, 0, 0.1);
  animation: card-entrance 0.6s var(--ease-out-expo) both;
  position: relative;
}

@keyframes card-entrance {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 17px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  pointer-events: none;
  z-index: 1;
}

.card-top {
  padding: 40px 32px 24px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.5);
  animation: fade-up 0.6s var(--ease-out-expo) both;
  animation-delay: 0.1s;
}

.card-middle {
  padding: 20px 32px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  animation: fade-up 0.6s var(--ease-out-expo) both;
  animation-delay: 0.2s;
}

.card-bottom {
  padding: 16px 32px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid rgba(255, 255, 255, 0.5);
  animation: fade-up 0.6s var(--ease-out-expo) both;
  animation-delay: 0.3s;
}

.login-header {
  display: flex;
  align-items: center;
  gap: 14px;
}

.logo-icon {
  width: 64px;
  height: 64px;
  background: #b45309;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(180, 83, 9, 0.3);
  flex-shrink: 0;
  animation: fade-up 0.6s var(--ease-out-expo) both;
  animation-delay: 0.15s;
}

.logo-text {
  flex: 1;
  min-width: 0;
}

.login-title {
  font-size: 26px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 2px;
  letter-spacing: 0.02em;
}

.login-subtitle {
  font-size: 12px;
  color: #6b7280;
}

.login-form {
  margin-bottom: 0;
}

.input-group {
  margin-bottom: 4px;
  animation: fade-up 0.6s var(--ease-out-expo) both;
}
.input-group:nth-child(1) { animation-delay: 0.25s; }
.input-group:nth-child(2) { animation-delay: 0.3s; }

.input-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 6px;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  animation: fade-up 0.6s var(--ease-out-expo) both;
  animation-delay: 0.32s;
}

.login-btn {
  width: 100%;
  height: 46px;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  background: #b45309;
  border-color: #b45309;
  transition: all 0.2s var(--ease-out-expo);
  letter-spacing: 0.04em;
  position: relative;
  overflow: hidden;
  animation: fade-up 0.6s var(--ease-out-expo) both;
  animation-delay: 0.35s;
}

.login-btn:hover {
  background: #92400e;
  border-color: #92400e;
  box-shadow: 0 4px 16px rgba(180, 83, 9, 0.3);
  transform: translateY(-1px);
}

.login-btn:active {
  transform: translateY(0) scale(0.98);
  box-shadow: 0 2px 8px rgba(180, 83, 9, 0.2);
  filter: brightness(0.95);
}

.login-card :deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 0 0 1px #e5e7eb;
  transition: all 0.25s var(--ease-out-expo) !important;
}

.login-card :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #d1d5db;
}

.login-card :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px #b45309, 0 0 16px rgba(180, 83, 9, 0.12) !important;
}

.register-link {
  text-align: center;
  font-size: 13px;
  color: #6b7280;
}

.register-link a {
  color: #b45309;
  margin-left: 4px;
  cursor: pointer;
  font-weight: 500;
}

.register-link a:hover {
  text-decoration: underline;
}
</style>
