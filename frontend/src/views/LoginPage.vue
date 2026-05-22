<template>
  <div class="login-container">
    <div class="login-left">
      <div class="login-card">
        <div class="login-header">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M7 20h10"/>
              <path d="M12 20v-8"/>
              <path d="M12 12c-3-3-6-2-7 1 3 0 5-1 7-1"/>
              <path d="M12 12c3-3 6-2 7 1-3 0-5-1-7-1"/>
              <path d="M12 8c-2-4-5-4-6-1"/>
              <path d="M12 8c2-4 5-4 6-1"/>
            </svg>
          </div>
          <h1 class="login-title">农作物病虫害检测平台</h1>
          <p class="login-subtitle">智能识别 · 精准防护</p>
        </div>

        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          class="login-form"
        >
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入用户名"
              size="large"
            >
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              size="large"
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item class="form-actions">
            <el-checkbox v-model="loginForm.remember">记住我</el-checkbox>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" size="large" class="login-btn" :loading="loading" @click="handleLogin">
              登录
            </el-button>
          </el-form-item>
        </el-form>

        <div class="register-link">
          <span>还没有账号？</span>
          <router-link to="/register">立即注册</router-link>
        </div>
      </div>
    </div>

    <div class="login-right">
      <div class="overlay">
        <div class="brand-text">
          <h2>守护农作物健康</h2>
          <p>基于深度学习的智能病虫害检测系统</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { User, Lock } from "@element-plus/icons-vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useUserStore } from "../stores/user";

const router = useRouter();
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
        });
        if (res.success) {
          ElMessage.success("登录成功");
          router.push("/dashboard");
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
}

.login-left {
  width: 35%;
  min-width: 400px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  padding: 40px;
}

.login-card {
  width: 100%;
  max-width: 380px;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-icon {
  width: 60px;
  height: 60px;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, #0d9488 0%, #14b8a6 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-title {
  font-size: 22px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 6px;
}

.login-subtitle {
  font-size: 13px;
  color: #6b7280;
}

.login-form {
  margin-bottom: 24px;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.login-btn {
  width: 100%;
  height: 44px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
  background: linear-gradient(135deg, #0d9488 0%, #14b8a6 100%);
  border-color: #0d9488;
}

.login-btn:hover {
  background: linear-gradient(135deg, #0f766e 0%, #0d9488 100%);
}

.register-link {
  text-align: center;
  font-size: 13px;
  color: #6b7280;
}

.register-link a {
  color: #0d9488;
  margin-left: 4px;
  cursor: pointer;
}

.register-link a:hover {
  text-decoration: underline;
}

.login-right {
  flex: 1;
  background: url('/login-bg.jpg') center/cover no-repeat;
  position: relative;
}

.overlay {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.2);
}

.brand-text {
  text-align: center;
  color: #ffffff;
}

.brand-text h2 {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 12px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.brand-text p {
  font-size: 16px;
  opacity: 0.9;
}
</style>
