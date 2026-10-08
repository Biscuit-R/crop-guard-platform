<template>
  <div class="register-container">
    <div class="register-card">
      <div class="register-header">
        <div class="logo-icon">
          <el-icon :size="40" color="#ffffff"><UserFilled /></el-icon>
        </div>
        <h1 class="register-title">创建账号</h1>
        <p class="register-subtitle">加入我们，开启智能植保之旅</p>
      </div>

      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        class="register-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="请输入用户名"
            size="large"
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="phone">
          <el-input
            v-model="registerForm.phone"
            placeholder="请输入手机号"
            size="large"
            maxlength="11"
          >
            <template #prefix>
              <el-icon><Iphone /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="code">
          <div class="code-row">
            <el-input
              v-model="registerForm.code"
              placeholder="请输入验证码"
              size="large"
              maxlength="6"
            >
              <template #prefix>
                <el-icon><Key /></el-icon>
              </template>
            </el-input>
            <el-button
              type="primary"
              size="large"
              class="code-btn"
              :disabled="countdown > 0"
              @click="handleSendCode"
            >
              {{ countdown > 0 ? `${countdown}s 后重发` : "发送验证码" }}
            </el-button>
          </div>
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            show-password
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="请确认密码"
            size="large"
            show-password
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item class="agree-terms">
          <el-checkbox v-model="registerForm.agree" />
          <span>我已阅读并同意</span>
          <a href="#" class="terms-link">《服务条款》</a>
          <span>和</span>
          <a href="#" class="terms-link">《隐私政策》</a>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" size="large" class="register-btn" @click="handleRegister">
            注册
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-link">
        <span>已有账号？</span>
        <router-link to="/login">立即登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onBeforeUnmount } from "vue";
import { UserFilled, User, Lock, Iphone, Key } from "@element-plus/icons-vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { useUserStore } from "../stores/user";
import { sendSmsCode } from "../api/sms";

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

const registerForm = reactive({
  username: "",
  phone: "",
  code: "",
  password: "",
  confirmPassword: "",
  agree: false,
});

const registerRules = {
  username: [
    { required: true, message: "请输入用户名", trigger: "blur" },
    { min: 3, max: 20, message: "用户名长度在3到20个字符", trigger: "blur" },
    { pattern: /^[a-zA-Z0-9_]+$/, message: "用户名只能包含字母、数字和下划线", trigger: "blur" },
  ],
  phone: [
    { required: true, message: "请输入手机号", trigger: "blur" },
    { pattern: /^1\d{10}$/, message: "请输入正确的 11 位手机号", trigger: "blur" },
  ],
  code: [
    { required: true, message: "请输入验证码", trigger: "blur" },
    { pattern: /^\d{6}$/, message: "验证码为 6 位数字", trigger: "blur" },
  ],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 8, max: 30, message: "密码长度在8到30个字符", trigger: "blur" },
    { pattern: /^(?=.*[a-zA-Z])(?=.*\d)/, message: "密码需包含字母和数字", trigger: "blur" },
  ],
  confirmPassword: [
    { required: true, message: "请确认密码", trigger: "blur" },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error("两次输入的密码不一致"));
        } else {
          callback();
        }
      },
      trigger: "blur",
    },
  ],
  agree: [
    {
      validator: (rule, value, callback) => {
        if (!value) {
          callback(new Error("请同意服务条款和隐私政策"));
        } else {
          callback();
        }
      },
      trigger: "change",
    },
  ],
};

const registerFormRef = ref(null);
const loading = ref(false);
const countdown = ref(0);
let countdownTimer = null;

// 发送验证码：演示模式下后端把验证码随响应返回，这里弹窗展示
// （省去真实短信网关；倒计时期间按钮禁用防连发，后端另有 60s 间隔兜底）
const handleSendCode = () => {
  registerFormRef.value.validateField("phone", async (errMsg) => {
    if (errMsg) return;
    try {
      const res = await sendSmsCode(registerForm.phone);
      if (res.code) {
        ElMessageBox.alert(
          `演示模式：未接入真实短信网关，本次验证码为 ${res.code}（5 分钟内有效）`,
          "验证码",
          { confirmButtonText: "知道了", type: "info" }
        );
      } else {
        ElMessage.success("验证码已发送，请注意查收");
      }
      countdown.value = 60;
      countdownTimer = setInterval(() => {
        countdown.value -= 1;
        if (countdown.value <= 0) clearInterval(countdownTimer);
      }, 1000);
    } catch (error) {
      // 错误已在 axios 拦截器中处理（429 频率限制等）
    }
  });
};

const handleRegister = () => {
  registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        const res = await userStore.register({
          username: registerForm.username,
          phone: registerForm.phone,
          code: registerForm.code,
          password: registerForm.password,
        });
        if (res.success) {
          ElMessage.success("注册成功");
          const redirect = route.query.redirect;
          router.push(redirect || "/detection");
        }
      } catch (error) {
        // 错误已在 axios 拦截器中处理
      } finally {
        loading.value = false;
      }
    }
  });
};

onBeforeUnmount(() => {
  if (countdownTimer) clearInterval(countdownTimer);
});
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-color);
}

.register-card {
  width: 100%;
  max-width: 420px;
  padding: 40px;
  background: var(--surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--card-shadow);
}

.register-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-icon {
  width: 60px;
  height: 60px;
  margin: 0 auto 16px;
  background: #b45309;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.register-title {
  font-size: 22px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 6px;
}

.register-subtitle {
  font-size: 13px;
  color: #6b7280;
}

.register-form {
  margin-bottom: 24px;
}

.code-row {
  display: flex;
  gap: 8px;
  width: 100%;
}

.code-btn {
  white-space: nowrap;
  border-radius: 10px;
  background: #b45309;
  border-color: #b45309;
}

.code-btn:hover {
  background: #92400e;
  border-color: #92400e;
}

.agree-terms {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 16px;
}

.terms-link {
  color: #b45309;
  margin: 0 4px;
}

.terms-link:hover {
  text-decoration: underline;
}

.register-btn {
  width: 100%;
  height: 44px;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 500;
  background: #b45309;
  border-color: #b45309;
  transition: background 0.2s ease;
}

.register-btn:hover {
  background: #92400e;
  border-color: #92400e;
}

.login-link {
  text-align: center;
  font-size: 13px;
  color: #6b7280;
}

.login-link a {
  color: #b45309;
  margin-left: 4px;
}

.login-link a:hover {
  text-decoration: underline;
}
</style>
