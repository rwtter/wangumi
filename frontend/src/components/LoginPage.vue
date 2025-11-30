<template>
  <div class="login-container">
    <h1>用户登录</h1>
    <form @submit.prevent="handleLogin">
      <div class="form-group">
        <label>用户名</label>
        <input
          v-model.trim="account"
          type="text"
          placeholder="请输入用户名"
          :class="{ 'is-invalid': errors.account }"
        />
        <p v-if="errors.account" class="error">{{ errors.account }}</p>
      </div>

      <div class="form-group">
        <label>密码</label>
        <input
          v-model.trim="password"
          type="password"
          placeholder="请输入密码"
          :class="{ 'is-invalid': errors.password }"
        />
        <p v-if="errors.password" class="error">{{ errors.password }}</p>
      </div>

      <button type="submit" class="btn-login">登录</button>

      <p v-if="message" class="success">{{ message }}</p>
     
      <div class="actions">
        <button type="button" class="link-btn" @click="goRegister">注册</button> 
        <button type="button" class="link-btn" @click="goForgotPassword">忘记密码？</button>
      </div>

    </form>
  </div>
</template>


<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const errors = ref({ account: '', password: '' })

// 响应式变量
const account = ref('')
const password = ref('')
const message = ref('')
const router = useRouter()

//跳转到注册页面
function goRegister() {
  router.push('/register')
}

//跳转到忘记密码页面
function goForgotPassword() {
  router.push('/forgot-password')
}

 
// 带自动刷新功能的 fetch 封装
async function fetchWithAuth(url, options = {}, retry = true) {
  const accessToken = localStorage.getItem('access_token')
  options.headers = {
    ...(options.headers || {}),
    Authorization: `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
  }

  const response = await fetch(url, options)

  // 若 access token 过期（401），尝试刷新一次
  if (response.status === 401 && retry) {
    const refreshed = await refreshAccessToken()
    if (refreshed) {
      return fetchWithAuth(url, options, false)
    }
  }

  return response
}

 
// 新增：刷新 access token
async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) {
    // 如果连 refresh token 都没有，说明用户需要重新登录
    console.warn('未找到 refresh token，需要重新登录')
    router.push('/login') // 跳转回登录页
    return false
  }

  try {
    const res = await fetch('/api/token/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken }),
    })

    if (!res.ok) {
      // 如果刷新失败（比如refresh token过期），清除所有token并跳转登录
      console.error('Refresh token 无效或已过期')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      router.push('/login')
      return false
    }

    const data = await res.json()

    if (data.access) {
      localStorage.setItem('access_token', data.access)
      console.log('✅ Access token 已刷新')
      return true
    }
  } catch (err) {
    console.error('刷新 access token 失败:', err)
    // 网络错误等异常情况，也做同样处理
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    router.push('/login')
  }

  return false
}


 
// 登录
async function handleLogin() {
  message.value = ''
  try {
    const res = await fetch('/api/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: account.value,
        password: password.value,
      }),
    })

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}))
      message.value = errData.detail || '登录失败'
      return
    }

    const data = await res.json()
    console.log('登录接口返回的数据:', data)
    if (data.access && data.refresh) {
      // 存储 token
      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)
      console.log('存储的 refresh_token:', data.refresh)
      message.value = '登录成功，正在跳转...'

      // 跳转到 /animelist
      setTimeout(() => {
        router.push('/animelist')
      }, 1000)
    } else {
      message.value = '服务器未返回 token'
    }
  } catch (error) {
    console.error('登录错误:', error)
    message.value = '网络错误'
  }
}

 
/* async function handleLogout() {
  message.value = ''
  try {
    const res = await fetchWithAuth('/api/logout/', { method: 'POST' })

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}))
      // ⭐ 如果是401错误，说明token已失效，直接清除并跳转
      if (res.status === 401) {
        console.warn('登出时token已失效，直接清除本地状态')
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        router.push('/login')
        return
      }
      message.value = errData.message || '登出失败'
      return
    }

    const data = await res.json()
    message.value = data.message || '登出成功'

    // ⭐ 清除本地 token
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    
    // ⭐ 登出成功后跳转到登录页
    setTimeout(() => {
      router.push('/login')
    }, 1000)
  } catch (err) {
    console.error('登出错误:', err)
    message.value = '登出失败'
  }
} */

</script>


<style scoped>
.success { color: #28a745; margin-top: 12px; }
.login-container {
  width: 500px;
  margin: 100px auto;
  padding: 30px;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

h1 {
  text-align: center;
  color: #e58c8c;
  margin-bottom: 30px;
}
label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #555;
  text-align: left;
}
.form-group {
  margin-bottom: 20px;
}
input {
  width: 95%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
}
input.is-invalid {
  border-color: #e74c3c;
}
.error {
  color: #e74c3c;
  font-size: 12px;
}
.btn-login {
  width: 100%;
  background-color: #ec92bf; 
  color: white;
  padding: 10px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.actions {
  display: flex;
  justify-content: space-between;
  margin-top: 15px;
}
.link-btn {
  border: none;
  background: none;
  color: #ec92bf;
  cursor: pointer;
}

</style>
