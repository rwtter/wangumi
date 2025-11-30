<template>
  <div class="forgot-container">
    <h2>找回密码</h2>

    <!-- Part 1: 输入邮箱 -->
    <div class="form-section">
      <div class="form-group">
        <label for="email">邮箱</label>
        <input
          id="email"
          type="email"
          v-model.trim="form.email"
          @blur="validateEmail"
          @input="errors.email = ''"
          placeholder="请输入您的邮箱地址"
          :class="{ 'is-invalid': errors.email }"
          :disabled="isCodeSent"
        />
        <p v-if="errors.email" class="error-message">{{ errors.email }}</p>
      </div>

      <button @click="sendVerificationCode" :disabled="isCodeSending || countdown > 0 || !isEmailValid || isCodeSent">
        {{ isCodeSent ? '已发送' : (countdown > 0 ? `${countdown}s后重发` : (isCodeSending ? '发送中...' : '发送验证码')) }}
      </button>
    </div>

    <!-- Part 2: 输入验证码和新密码 (在验证码发送后才显示) -->
    <div v-if="isCodeSent" class="form-section">
      <p class="info-message">验证码已发送至 {{ form.email }}</p>
      
      <div class="form-group">
        <label for="code">验证码</label>
        <input
          id="code"
          type="text"
          v-model.trim="form.code"
          placeholder="请输入6位验证码"
          maxlength="6"
          :class="{ 'is-invalid': errors.verificationCode }"
        />
        <p v-if="errors.verificationCode" class="error-message">{{ errors.verificationCode }}</p>
      </div>

      <div class="form-group">
        <label for="new-password">新密码</label>
        <input
          id="new-password"
          type="password"
          v-model="newPassword"
          placeholder="请输入新密码（至少6位）"
          @input="checkStrength"
          :class="{ 'is-invalid': errors.newPassword }"
        />
        <p v-if="errors.newPassword" class="error-message">{{ errors.newPassword }}</p>
      </div>

      <div class="form-group">
        <label for="confirm-password">确认新密码</label>
        <input
          id="confirm-password"
          type="password"
          v-model="confirmPassword"
          placeholder="请再次输入新密码"
          :class="{ 'is-invalid': errors.confirmPassword }"
        />
        <p v-if="errors.confirmPassword" class="error-message">{{ errors.confirmPassword }}</p>
      </div>
      
      <p class="info-message strength">{{ strengthMsg }}</p>

      <button @click="resetPassword" :disabled="!isFormValid || isSubmitting">
        {{ isSubmitting ? '提交中...' : '确认重置' }}
      </button>
    </div>

    <!-- Part 3: 成功提示 (在重置成功后显示) -->
    <div v-if="isSuccess" class="success-overlay">
      <div class="success-step">
        <h3>✅ 重置成功！</h3>
        <p>您的密码已重置，请使用新密码登录。</p>
        <button @click="$router.push('/login')">返回登录</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";

const form = ref({
  email: '',
  code: ''
});

const newPassword = ref('');
const confirmPassword = ref('');
const strengthMsg = ref('');

const errors = ref({
  email: '',
  verificationCode: '',
  newPassword: '',
  confirmPassword: ''
});

const isCodeSending = ref(false);
const isSubmitting = ref(false);
const countdown = ref(0);
const isCodeSent = ref(false);
const isSuccess = ref(false);

// 使用相对路径，方便本地开发（通过 Vite 代理到 8000）和线上部署（由 Nginx 反向代理）
const API_BASE = '';

// --- 计算属性 ---
const isEmailValid = computed(() => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.value.email);
});

const isFormValid = computed(() => {
  return isCodeSent.value &&
         form.value.code.length === 6 && 
         newPassword.value.length >= 6 && 
         newPassword.value === confirmPassword.value &&
         !errors.value.newPassword &&
         !errors.value.confirmPassword;
});

// --- 方法定义 ---
function validateEmail() {
  if (!form.value.email) {
    errors.value.email = '邮箱不能为空';
  } else if (!isEmailValid.value) {
    errors.value.email = '请输入有效的邮箱地址';
  } else {
    errors.value.email = '';
  }
}

function checkStrength() {
  const p = newPassword.value;
  if (p.length < 6) {
    strengthMsg.value = "密码太短";
    errors.value.newPassword = '密码长度至少6位';
  } else if (!/[A-Z]/.test(p) || !/[0-9]/.test(p)) {
    strengthMsg.value = "建议包含大写字母和数字";
    errors.value.newPassword = '';
  } else {
    strengthMsg.value = "密码强度良好";
    errors.value.newPassword = '';
  }
  if (confirmPassword.value && p !== confirmPassword.value) {
    errors.value.confirmPassword = '两次输入的密码不一致';
  } else {
    errors.value.confirmPassword = '';
  }
}

async function sendVerificationCode() {
  validateEmail();
  if (!isEmailValid.value) return;

  isCodeSending.value = true;
  errors.value.email = '';

  try {
    const response = await fetch(`${API_BASE}/api/password_reset/request/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: form.value.email }),
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error || '发送验证码失败');
    }

    isCodeSent.value = true;
    countdown.value = 60;
    const timer = setInterval(() => {
      countdown.value--;
      if (countdown.value <= 0) clearInterval(timer);
    }, 1000);

  } catch (err) {
    console.error('发送验证码失败', err);
    errors.value.email = err.message || '发送验证码失败，请稍后重试';
  } finally {
    isCodeSending.value = false;
  }
}

async function resetPassword() {
  if (newPassword.value !== confirmPassword.value) {
    errors.value.confirmPassword = '两次输入的密码不一致';
    return;
  }

  isSubmitting.value = true;
  errors.value.verificationCode = '';

  try {
    const response = await fetch(`${API_BASE}/api/password_reset/confirm/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: form.value.email,
        code: form.value.code,
        new_password: newPassword.value,
      }),
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error || '重置密码失败');
    }

    isSuccess.value = true;

  } catch (err) {
    console.error('重置密码失败', err);
    errors.value.verificationCode = err.message || '重置密码失败，请检查验证码或稍后重试';
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<style scoped>
.forgot-container {
  background-color: #ffffff;
  width: 500px;
  padding: 40px 32px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  margin: 60px auto;
  position: relative;
}
h2 {
  text-align: center;
  color: #e58c8c;
  margin-bottom: 30px;
}
.form-section {
  margin-bottom: 20px;
}
.form-group {
  margin-bottom: 20px;
}
label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #555;
}
/* 统一所有输入框样式 */
input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  box-sizing: border-box;
  font-size: 16px;
  transition: border-color 0.3s;
}
input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}
input:focus {
  outline: none;
  border-color: #e58c8c;
}
input.is-invalid {
  border-color: #dc3545;
}

/* 统一所有提示信息样式 */
.error-message {
  color: #dc3545;
  font-size: 12px;
  margin-top: 5px;
  min-height: 16px; /* 使用min-height防止布局跳动 */
}
.info-message {
  font-size: 13px;
  color: #555;
  margin: 8px 0;
  min-height: 20px; /* 使用min-height防止布局跳动 */
}
.strength {
  color: #888; /* 密码强度提示可以稍微区别于普通信息 */
}

button {
  margin-top: 10px;
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 6px;
  background-color: #ec92bf;
  color: white;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s;
}
button:hover:not(:disabled) {
  background-color: #d67fa9;
}
button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

/* 成功提示覆盖层 */
.success-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.95);
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 12px;
}
.success-step {
  text-align: center;
}
.success-step h3 {
  color: #28a745;
  margin-bottom: 16px;
}
.success-step p {
  color: #666;
  margin-bottom: 20px;
}
</style>
