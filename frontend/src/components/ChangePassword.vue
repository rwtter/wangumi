<template>
  <div class="change-container">
    <h2>修改密码</h2>

    <div class="password-form">
      <div class="input-group">
        <label for="old-password">当前密码</label>
        <input
          id="old-password"
          type="password"
          v-model="oldPassword"
          placeholder="请输入当前密码"
          :class="{ 'is-invalid': errors.oldPassword }"
        />
        <p v-if="errors.oldPassword" class="error-message">{{ errors.oldPassword }}</p>
      </div>

      <div class="input-group">
        <label for="new-password">新密码</label>
        <input
          id="new-password"
          :type="showNew ? 'text' : 'password'"
          v-model="newPassword"
          placeholder="请输入新密码"
          @input="checkStrength"
          :class="{ 'is-invalid': errors.newPassword }"
        />
        <button type="button" class="toggle" @click="showNew = !showNew">
          {{ showNew ? '隐藏' : '显示' }}
        </button>
      </div>

      <div class="input-group">
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

      <p class="strength">{{ strengthMsg }}</p>

      <button @click="submitNewPassword" :disabled="loading">
        {{ loading ? '提交中...' : '确认修改' }}
      </button>
    </div>

    <!-- 成功反馈 -->
    <div v-if="showSuccess" class="success-overlay">
      <div class="success-step">
        <h3>✅ 修改成功！</h3>
        <p>为了安全，请重新登录。</p>
        <button @click="logoutAndRedirect">返回登录</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from 'vue-router';

const router = useRouter();

const oldPassword = ref("");
const newPassword = ref("");
const confirmPassword = ref("");
const strengthMsg = ref("");
const showNew = ref(false);
const loading = ref(false);
const showSuccess = ref(false);

const errors = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
});

// 使用相对路径，适配本地代理和线上反向代理
const API_BASE = '';

function getAuthToken() {
  return localStorage.getItem('access_token');
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
}

async function submitNewPassword() {
  // 重置错误信息
  errors.value = { oldPassword: '', newPassword: '', confirmPassword: '' };
  let hasError = false;

  if (!oldPassword.value) {
    errors.value.oldPassword = '请输入当前密码';
    hasError = true;
  }
  if (!newPassword.value) {
    errors.value.newPassword = '请输入新密码';
    hasError = true;
  }
  if (newPassword.value !== confirmPassword.value) {
    errors.value.confirmPassword = '两次输入的密码不一致';
    hasError = true;
  }
  if (hasError) return;

  loading.value = true;
  try {
    const params = new URLSearchParams();
    params.append('old_password', oldPassword.value);
    params.append('new_password', newPassword.value);

    const res = await fetch(`${API_BASE}/api/account/password_change/`, {
      method: "POST",
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: params,
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data?.error || data?.detail || "修改密码失败，请重试。");
    }

    // 成功，显示成功提示
    showSuccess.value = true;

  } catch (err) {
    console.error('修改密码失败:', err);
    if (err.message.includes('old_password')) {
      errors.value.oldPassword = '当前密码错误';
    } else {
      strengthMsg.value = err.message;
    }
  } finally {
    loading.value = false;
  }
}

function logoutAndRedirect() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  window.dispatchEvent(new CustomEvent('user-logged-out'));
  setTimeout(() => {
    router.push('/login');
  }, 1000);
}
</script>

<style scoped>
.change-container {
  background-color: #ffffff;
  width: 400px;
  padding: 40px 32px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  margin: 60px auto;
  position: relative; /* 为成功提示覆盖层做准备 */
}
h2 {
  text-align: center;
  color: #e58c8c;
  margin-bottom: 30px;
}
.input-group {
  margin-bottom: 20px;
  position: relative;
}
.input-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #555;
}
.input-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
  font-size: 14px;
  transition: border-color 0.3s;
}
.toggle {
  position: absolute;
  right: 12px;
  top: 42px;
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 0;
  width: auto;
  margin: 0;
}
button {
  margin-top: 12px;
  width: 100%;
  padding: 10px;
  background-color: #ec92bf;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.3s;
}
button:hover:not(:disabled) {
  background-color: #d67fa9;
}
button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
.strength {
  font-size: 13px;
  color: #555;
  margin: 8px 0;
  min-height: 20px;
}
.error-message {
  color: #dc3545;
  font-size: 12px;
  margin-top: 5px;
}
input:focus {
  outline: none;
  border-color: #e58c8c;
}
input.is-invalid {
  border-color: #dc3545;
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
