<template>
  <div class="modify-container">
    <h2>修改邮箱</h2>

    <!-- Step 1: 验证当前邮箱 -->
    <div v-if="step === 1">
      <p>请输入当前绑定的邮箱进行身份验证：</p>
      <div class="input-group">
        <input 
          v-model="currentEmail" 
          type="email" 
          placeholder="当前邮箱" 
          :class="{ 'is-invalid': errors.currentEmail }"
          @blur="validateCurrentEmail"
        />
        <div v-if="errors.currentEmail" class="field-error">{{ errors.currentEmail }}</div>
      </div> 
      
      <div class="verify-group">
        <input 
          v-model="currentEmailCode" 
          placeholder="邮箱验证码" 
          :class="{ 'is-invalid': errors.currentEmailCode }"
          @blur="validateCurrentEmailCode"
          maxlength="6"
        />
        <button @click="sendCurrentEmailCode" :disabled="countdownCurrent > 0 || loading || !currentEmail">
          {{ loading ? '发送中...' : (countdownCurrent > 0 ? countdownCurrent + 's后重发' : '发送验证码') }}
        </button>
      </div>
      <div v-if="errors.currentEmailCode" class="field-error">{{ errors.currentEmailCode }}</div>
      
      <button @click="goToStep2" :disabled="loading || !isStep1Valid">下一步</button>
    </div>

    <!-- Step 2: 输入新邮箱 -->
    <div v-else-if="step === 2">
      <p>请输入新的邮箱地址：</p>
      <div class="input-group">
        <input 
          v-model="newContact" 
          type="email" 
          placeholder="新邮箱" 
          :class="{ 'is-invalid': errors.newContact }"
          @blur="validateNewEmail"
        />
        <div v-if="errors.newContact" class="field-error">{{ errors.newContact }}</div>
      </div>
      
      <div class="input-group">
        <input 
          v-model="currentPassword" 
          type="password" 
          placeholder="当前密码" 
          :class="{ 'is-invalid': errors.currentPassword }"
          @blur="validatePassword"
        />
        <div v-if="errors.currentPassword" class="field-error">{{ errors.currentPassword }}</div>
      </div>


      <div class="verify-group">
        <input 
          v-model="newEmailCode" 
          placeholder="邮箱验证码" 
          :class="{ 'is-invalid': errors.newEmailCode }"
          @blur="validateNewEmailCode"
          maxlength="6"
        />
        <button @click="sendNewEmailCode" :disabled="countdownNew > 0 || loading || !isStep2EmailValid">
          {{ loading ? '发送中...' : (countdownNew > 0 ? countdownNew + 's后重发' : '发送验证码') }}
        </button>
      </div>
      <div v-if="errors.newEmailCode" class="field-error">{{ errors.newEmailCode }}</div>
      
      <button @click="confirmNewEmail" :disabled="loading || !isStep2Valid">确认修改</button>
    </div>

    <!-- Step 3: 成功提示 -->
    <div v-else class="success-step">
      <h3>✅ 修改成功</h3>
      <p>新的邮箱：{{ maskedNew }}</p>
      <button @click="$router.push('/personal')">返回个人中心</button>
    </div>

    <!-- 全局错误提示 -->
    <div v-if="errorMessage" class="error-message">
      {{ errorMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const step = ref(1)
const currentEmail = ref('')
const currentPassword = ref('')
const currentEmailCode = ref('')
const newContact = ref('')
const newEmailCode = ref('')
const countdownCurrent = ref(0)
const countdownNew = ref(0)
const loading = ref(false)
const errorMessage = ref('')

// 错误状态
const errors = ref({
  currentEmail: '',
  currentPassword: '',
  currentEmailCode: '',
  newContact: '',
  newEmailCode: ''
})

const maskedNew = ref('')

// 计算属性：验证各步骤是否有效
const isStep1Valid = computed(() => {
  return currentEmail.value && 
         validateEmail(currentEmail.value) &&  
         currentEmailCode.value && 
         currentEmailCode.value.length === 6 &&
         !errors.value.currentEmail && 
         !errors.value.currentPassword &&
         !errors.value.currentEmailCode
})

const isStep2EmailValid = computed(() => {
  return newContact.value && 
         validateEmail(newContact.value) && 
         newContact.value.toLowerCase() !== currentEmail.value.toLowerCase() &&
         !errors.value.newContact
})

const isStep2Valid = computed(() => {
  return isStep2EmailValid.value && 
         newEmailCode.value && 
         newEmailCode.value.length === 6 &&
         !errors.value.newEmailCode
})

// API基础URL：使用相对路径，便于本地（Vite 代理）和线上（Nginx 反向代理）统一
const API_BASE = ''

// 验证邮箱格式
function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(email)
}

// 清除所有错误
function clearErrors() {
  errors.value = {
    currentEmail: '',
    currentPassword: '',
    currentEmailCode: '',
    newContact: '',
    newEmailCode: ''
  }
  errorMessage.value = ''
}

// 验证当前邮箱
function validateCurrentEmail() {
  if (!currentEmail.value) {
    errors.value.currentEmail = '请输入当前邮箱'
    return false
  }
  if (!validateEmail(currentEmail.value)) {
    errors.value.currentEmail = '请输入有效的邮箱地址'
    return false
  }
  errors.value.currentEmail = ''
  return true
}

// 验证密码
function validatePassword() {
  if (!currentPassword.value) {
    errors.value.currentPassword = '请输入当前密码'
    return false
  }
  if (currentPassword.value.length < 6) {
    errors.value.currentPassword = '密码长度至少6位'
    return false
  }
  errors.value.currentPassword = ''
  return true
}

// 验证当前邮箱验证码
function validateCurrentEmailCode() {
  if (!currentEmailCode.value) {
    errors.value.currentEmailCode = '请输入验证码'
    return false
  }
  if (currentEmailCode.value.length !== 6) {
    errors.value.currentEmailCode = '请输入6位验证码'
    return false
  }
  errors.value.currentEmailCode = ''
  return true
}

// 验证新邮箱
function validateNewEmail() {
  if (!newContact.value) {
    errors.value.newContact = '请输入新邮箱'
    return false
  }
  if (!validateEmail(newContact.value)) {
    errors.value.newContact = '请输入有效的邮箱地址'
    return false
  }
  if (newContact.value.toLowerCase() === currentEmail.value.toLowerCase()) {
    errors.value.newContact = '新邮箱不能与当前邮箱相同'
    return false
  }
  errors.value.newContact = ''
  return true
}

// 验证新邮箱验证码
function validateNewEmailCode() {
  if (!newEmailCode.value) {
    errors.value.newEmailCode = '请输入验证码'
    return false
  }
  if (newEmailCode.value.length !== 6) {
    errors.value.newEmailCode = '请输入6位验证码'
    return false
  }
  errors.value.newEmailCode = ''
  return true
}

// 获取认证token
function getAuthToken() {
  return localStorage.getItem('access_token')
}

// 发送当前邮箱验证码（使用通用接口）
async function sendCurrentEmailCode() {
  if (!validateCurrentEmail()) return
  
  loading.value = true
  errorMessage.value = ''
  
  try {
    console.log(`正在向 ${currentEmail.value} 发送验证码`)
    
    const response = await fetch(`${API_BASE}/api/send_verification_code/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: currentEmail.value
      })
    })
    
    const text = await response.text()
    console.log('发送验证码响应:', text)
    
    let returnedCode = null
    try {
      const parsed = text ? JSON.parse(text) : null
      if (parsed) {
        if (typeof parsed === 'object' && parsed.code) returnedCode = String(parsed.code)
        else if (typeof parsed === 'string') returnedCode = parsed
      }
    } catch (e) {
      if (text && /\d{4,6}/.test(text)) returnedCode = text.match(/\d{4,6}/)?.[0] || null
    }
    
    if (!response.ok) {
      throw new Error('发送验证码失败')
    }
    
    if (returnedCode) {
      console.log(`验证码已发送到邮箱 ${currentEmail.value} (服务器返回验证码: ${returnedCode})`)
    } else {
      console.log(`验证码已发送到邮箱 ${currentEmail.value}（请查收）`)
    }
    
    // 开始倒计时
    countdownCurrent.value = 60
    const timer = setInterval(() => {
      countdownCurrent.value--
      if (countdownCurrent.value <= 0) clearInterval(timer)
    }, 1000)
    
  } catch (error) {
    errorMessage.value = '发送验证码失败，请重试'
    console.error('Error:', error)
  } finally {
    loading.value = false
  }
}


function goToStep2() {
  if (!isStep1Valid.value) return
  
  loading.value = true
  errorMessage.value = ''
  
  try {
    // 后端会验证邮箱和密码，前端直接进入下一步
    console.log('准备进入第二步，当前邮箱:', currentEmail.value)
    step.value = 2
  } catch (error) {
    errorMessage.value = '操作失败，请重试'
    console.error('Error:', error)
  } finally {
    loading.value = false
  }
}

/* // 验证当前邮箱（需要后端提供验证接口）
async function verifyCurrentEmail() {
  if (!validateCurrentEmailCode()) return
  
  loading.value = true
  errorMessage.value = ''
  
  try {
    const accessToken = getAuthToken()
    
    // 这里需要后端提供验证当前邮箱的接口
    // 暂时跳过验证，直接进入下一步
    console.log('验证当前邮箱:', {
      email: currentEmail.value,
      password: currentPassword.value,
      code: currentEmailCode.value
    })
    
    // TODO: 调用后端验证接口
    // const response = await fetch(`${API_BASE}/api/verify_current_email/`, {
    //   method: 'POST',
    //   headers: {
    //     'Content-Type': 'application/json',
    //     ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    //   },
    //   body: JSON.stringify({
    //     email: currentEmail.value,
    //     password: currentPassword.value,
    //     code: currentEmailCode.value
    //   })
    // })
    
    // 暂时直接进入下一步
    step.value = 2
    
  } catch (error) {
    errorMessage.value = '验证失败，请检查邮箱和验证码'
    console.error('Error:', error)
  } finally {
    loading.value = false
  }
}
 */
// 发送新邮箱验证码（使用修改邮箱接口）
async function sendNewEmailCode() {
  if (!validateNewEmail()) return
  
  loading.value = true
  errorMessage.value = ''
  
  try { 
    const accessToken = getAuthToken()
    if (!accessToken) {
        throw new Error('用户未登录，请先登录')
    }

    console.log('发送新邮箱验证码请求参数:', {
      contact_type: 'email',
      current_password: currentPassword.value,
      value: newContact.value
    })
    
    const response = await fetch(`${API_BASE}/api/account/contact/change/request/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      },
      body: JSON.stringify({
        contact_type: 'email',
        current_password: currentPassword.value,
        value: newContact.value
      })
    })
    
    console.log('发送新邮箱验证码响应状态:', response.status)
    
    let result
    try {
      result = await response.json()
      console.log('发送新邮箱验证码响应数据:', result)
    } catch (e) {
      console.log('响应不是JSON格式')
      result = { message: '服务器响应格式错误' }
    }
    
    if (!response.ok) {
      const errorMsg = result.error || result.detail || result.message || '发送验证码失败'
      throw new Error(errorMsg)
    }
    
    // 开始倒计时
    countdownNew.value = 60
    const timer = setInterval(() => {
      countdownNew.value--
      if (countdownNew.value <= 0) clearInterval(timer)
    }, 1000)
    
  } catch (error) {
    errorMessage.value = error.message || '发送验证码失败，请重试'
    console.error('Error:', error)
  } finally {
    loading.value = false
  }
}

// 确认新邮箱（使用修改邮箱确认接口）
async function confirmNewEmail() {
  if (!validateNewEmailCode()) return
  
  loading.value = true
  
  try {
    const accessToken = getAuthToken()
    if (!accessToken) {
        throw new Error('用户未登录，请先登录')
    }
    
    console.log('确认新邮箱请求参数:', {
      contact_type: 'email',
      value: newContact.value,
      code: newEmailCode.value,
      current_password: currentPassword.value
    })
    
    const response = await fetch(`${API_BASE}/api/account/contact/change/confirm/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      },
      body: JSON.stringify({
        contact_type: 'email',
        value: newContact.value,
        code: newEmailCode.value,
        current_password: currentPassword.value
      })
    })
    
    console.log('确认新邮箱响应状态:', response.status)
    
    let result
    try {
      result = await response.json()
      console.log('确认新邮箱响应数据:', result)
    } catch (e) {
      console.log('响应不是JSON格式')
      result = { message: '服务器响应格式错误' }
    }
    
    if (!response.ok) {
      const errorMsg = result.error || result.detail || result.message || '修改失败'
      throw new Error(errorMsg)
    }
    
    step.value = 3
    maskedNew.value = newContact.value.replace(/(.{2}).+(@.+)/, '$1****$2')
    
  } catch (error) {
    errorMessage.value = error.message || '修改失败，请重试'
    console.error('Error:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.modify-container {
  background-color: #ffffff;
  width: 400px;
  padding: 36px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  margin: 60px auto;
}

.input-group {
  margin-bottom: 16px;
}

.input-group input {
  width: 100%;
  height: 40px;
  padding: 10px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
  font-size: 14px;
  transition: border-color 0.3s;
}

.verify-group {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  margin-bottom: 16px;
}

.verify-group input {
  flex: 1;
  height: 40px;
  box-sizing: border-box;
  padding: 0 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.verify-group button {
  height: 40px;
  box-sizing: border-box;
  margin-top: 0;
  padding: 0 12px;
  white-space: nowrap;
}

button {
  margin-top: 12px;
  width: 100%;
  padding: 8px;
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

h2 {
  text-align: center;
  color: #e58c8c;
  margin-bottom: 30px;
}

input:focus {
  outline: none;
  border-color: #e58c8c;
}

input.is-invalid {
  border-color: #dc3545;
}

.field-error {
  color: #dc3545;
  font-size: 12px;
  margin-top: 4px;
}

.error-message {
  color: #dc3545;
  font-size: 14px;
  margin-top: 10px;
  text-align: center;
  padding: 8px;
  background-color: #f8d7da;
  border-radius: 4px;
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
