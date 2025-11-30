<template>
  <div class="item-create-page">
    <div class="create-container">
      <!-- 头部 -->
      <div class="page-header">
        <button class="back-btn" @click="goBack">
          <i class="fas fa-arrow-left"></i>
          返回
        </button>
        <h1 class="page-title">创建新条目</h1>
      </div>

      <!-- 创建表单 -->
      <div class="create-form-wrapper">
        <form @submit.prevent="handleSubmit" class="create-form">
          <!-- 标题输入 -->
          <div class="form-group">
            <label class="form-label required">
              <i class="fas fa-heading"></i>
              条目标题
            </label>
            <input
              v-model="formData.title"
              type="text"
              class="form-input"
              placeholder="请输入条目标题"
              maxlength="200"
              @blur="validateTitle"
            />
            <span v-if="errors.title" class="error-text">{{ errors.title }}</span>
          </div>

          <!-- 图片上传 -->
          <div class="form-group">
            <label class="form-label required">
              <i class="fas fa-image"></i>
              条目图片
            </label>
            <div class="upload-area">
              <!-- 图片预览 -->
              <div v-if="previewUrl" class="image-preview">
                <img :src="previewUrl" alt="预览图片" class="preview-img" />
                <button
                  type="button"
                  class="remove-btn"
                  @click="removeImage"
                  title="移除图片"
                >
                  <i class="fas fa-times"></i>
                </button>
              </div>

              <!-- 上传按钮 -->
              <div v-else class="upload-placeholder">
                <input
                  ref="fileInput"
                  type="file"
                  accept="image/jpeg,image/jpg,image/png,image/webp"
                  class="file-input"
                  @change="handleFileSelect"
                />
                <div class="upload-content" @click="triggerFileInput">
                  <i class="fas fa-cloud-upload-alt"></i>
                  <p>点击或拖拽图片到这里</p>
                  <span class="upload-hint">支持 JPG, PNG, WEBP 格式</span>
                </div>
              </div>
            </div>
            <span v-if="errors.image" class="error-text">{{ errors.image }}</span>
          </div>

          <!-- 上传进度 -->
          <div v-if="uploading" class="upload-progress">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
            </div>
            <span class="progress-text">上传中... {{ uploadProgress }}%</span>
          </div>

          <!-- 提交按钮 -->
          <div class="form-actions">
            <button
              type="button"
              class="btn btn-cancel"
              @click="goBack"
              :disabled="submitting"
            >
              取消
            </button>
            <button
              type="submit"
              class="btn btn-submit"
              :disabled="submitting || uploading"
            >
              <i class="fas fa-check" v-if="!submitting"></i>
              <i class="fas fa-spinner fa-spin" v-else></i>
              {{ submitting ? '创建中...' : '创建条目' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { createItem } from '@/services/itemService.js'

const router = useRouter()

// 表单数据
const formData = reactive({
  title: '',
  image: null
})

// 错误信息
const errors = reactive({
  title: '',
  image: ''
})

// 状态管理
const previewUrl = ref('')
const uploading = ref(false)
const uploadProgress = ref(0)
const submitting = ref(false)
const fileInput = ref(null)

// 验证标题
const validateTitle = () => {
  errors.title = ''
  if (!formData.title.trim()) {
    errors.title = '请输入条目标题'
    return false
  }
  if (formData.title.length > 200) {
    errors.title = '标题长度不能超过200个字符'
    return false
  }
  return true
}

// 验证图片
const validateImage = () => {
  errors.image = ''
  if (!formData.image && !previewUrl.value) {
    errors.image = '请上传条目图片'
    return false
  }
  return true
}

// 验证所有字段
const validateForm = () => {
  const isTitleValid = validateTitle()
  const isImageValid = validateImage()
  return isTitleValid && isImageValid
}

// 触发文件选择
const triggerFileInput = () => {
  fileInput.value?.click()
}

// 处理文件选择
const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (!file) return

  // 验证文件类型
  const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
  if (!validTypes.includes(file.type)) {
    errors.image = '请上传 JPG, PNG 或 WEBP 格式的图片'
    return
  }

  // 验证文件大小（限制为10MB）
  const maxSize = 10 * 1024 * 1024
  if (file.size > maxSize) {
    errors.image = '图片大小不能超过 10MB'
    return
  }

  // 清除错误
  errors.image = ''

  // 保存文件
  formData.image = file

  // 生成预览
  const reader = new FileReader()
  reader.onload = (e) => {
    previewUrl.value = e.target.result
  }
  reader.readAsDataURL(file)
}

// 移除图片
const removeImage = () => {
  formData.image = null
  previewUrl.value = ''
  if (fileInput.value) {
    fileInput.value.value = ''
  }
  errors.image = ''
}

// 提交表单
const handleSubmit = async () => {
  // 验证表单
  if (!validateForm()) {
    return
  }

  // 检查登录状态
  const token = localStorage.getItem('access_token')
  if (!token) {
    alert('请先登录')
    router.push('/login')
    return
  }

  try {
    submitting.value = true

    // 直接创建条目，图片文件会一起上传
    const itemData = {
      title: formData.title.trim(),
      imageFile: formData.image, // 直接传递文件对象
      is_admin: false // 条目的 is_admin 为 false
    }

    const response = await createItem(itemData)

    // 创建成功，跳转到详情页
    if (response?.code === 0 || response?.code === 201) {
      // 显示成功提示
      showSuccessToast('条目创建成功！')

      // 跳转到条目详情页
      const itemId = response.data?.id
      if (itemId) {
        setTimeout(() => {
          router.push(`/item/${itemId}`)
        }, 1000)
      } else {
        // 如果没有返回ID，跳转到列表页
        setTimeout(() => {
          router.push('/items')
        }, 1000)
      }
    } else {
      throw new Error(response?.message || '创建失败')
    }
  } catch (error) {
    console.error('创建条目失败:', error)
    showErrorToast(error.message || '创建失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

// 显示成功提示
const showSuccessToast = (message) => {
  // 简单的Toast实现，可以后续替换为更完善的组件
  const toast = document.createElement('div')
  toast.className = 'toast toast-success'
  toast.innerHTML = `<i class="fas fa-check-circle"></i> ${message}`
  document.body.appendChild(toast)

  setTimeout(() => {
    toast.classList.add('show')
  }, 100)

  setTimeout(() => {
    toast.classList.remove('show')
    setTimeout(() => {
      document.body.removeChild(toast)
    }, 300)
  }, 3000)
}

// 显示错误提示
const showErrorToast = (message) => {
  const toast = document.createElement('div')
  toast.className = 'toast toast-error'
  toast.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`
  document.body.appendChild(toast)

  setTimeout(() => {
    toast.classList.add('show')
  }, 100)

  setTimeout(() => {
    toast.classList.remove('show')
    setTimeout(() => {
      document.body.removeChild(toast)
    }, 300)
  }, 3000)
}

// 返回
const goBack = () => {
  if (confirm('确定要离开吗？未保存的内容将会丢失。')) {
    router.back()
  }
}
</script>

<style scoped>
.item-create-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #ffcfe6, #c2e9fb);
  font-family: 'Mochiy Pop One', 'Arial Rounded MT Bold', sans-serif;
  padding: 20px;
}

.create-container {
  max-width: 800px;
  margin: 0 auto;
}

/* 页面头部 */
.page-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
}

.back-btn {
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid #ffc2d9;
  border-radius: 15px;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #ff6b9d;
  font-family: inherit;
  font-size: 14px;
  font-weight: 500;
}

.back-btn:hover {
  background: #ff6b9d;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 107, 157, 0.3);
}

.page-title {
  color: #333;
  font-size: 32px;
  text-shadow: 2px 2px 0 #ffc2d9;
  margin: 0;
}

/* 表单容器 */
.create-form-wrapper {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 25px;
  padding: 40px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
}

.create-form {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

/* 表单组 */
.form-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.form-label {
  color: #333;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-label.required::after {
  content: '*';
  color: #ff6b9d;
  margin-left: 4px;
}

.form-label i {
  color: #ff6b9d;
}

.form-input {
  padding: 15px 20px;
  border: 2px solid #ffc2d9;
  border-radius: 15px;
  font-family: inherit;
  font-size: 16px;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.9);
}

.form-input:focus {
  outline: none;
  border-color: #ff6b9d;
  box-shadow: 0 0 0 4px rgba(255, 107, 157, 0.1);
}

.form-input::placeholder {
  color: #bbb;
}

/* 上传区域 */
.upload-area {
  position: relative;
}

.file-input {
  display: none;
}

.upload-placeholder {
  border: 3px dashed #ffc2d9;
  border-radius: 20px;
  padding: 60px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.5);
}

.upload-placeholder:hover {
  border-color: #ff6b9d;
  background: rgba(255, 107, 157, 0.05);
}

.upload-content i {
  font-size: 48px;
  color: #ff6b9d;
  margin-bottom: 15px;
}

.upload-content p {
  color: #333;
  font-size: 18px;
  margin: 10px 0;
  font-weight: 500;
}

.upload-hint {
  color: #999;
  font-size: 14px;
}

/* 图片预览 */
.image-preview {
  position: relative;
  display: inline-block;
  max-width: 100%;
}

.preview-img {
  max-width: 100%;
  max-height: 400px;
  border-radius: 20px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
  border: 4px solid white;
}

.remove-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(255, 107, 157, 0.9);
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.remove-btn:hover {
  background: #ff4081;
  transform: scale(1.1);
}

/* 上传进度 */
.upload-progress {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: rgba(255, 194, 217, 0.3);
  border-radius: 10px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff6b9d, #a2d2ff);
  transition: width 0.3s ease;
  border-radius: 10px;
}

.progress-text {
  color: #666;
  font-size: 14px;
  text-align: center;
}

/* 错误提示 */
.error-text {
  color: #ff4081;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  animation: shake 0.3s ease;
}

.error-text::before {
  content: '⚠';
  font-size: 16px;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

/* 表单操作按钮 */
.form-actions {
  display: flex;
  gap: 20px;
  justify-content: flex-end;
  padding-top: 20px;
  border-top: 2px solid #ffc2d9;
}

.btn {
  padding: 14px 32px;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  font-family: inherit;
  font-size: 16px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

.btn-cancel {
  background: rgba(255, 255, 255, 0.9);
  color: #666;
  border: 2px solid #ddd;
}

.btn-cancel:hover:not(:disabled) {
  background: #f5f5f5;
  border-color: #bbb;
  transform: translateY(-2px);
}

.btn-submit {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 6px 18px rgba(255, 107, 157, 0.4);
}

/* Toast提示 */
.toast {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 16px 24px;
  border-radius: 15px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  font-weight: 500;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
  opacity: 0;
  transform: translateX(100px);
  transition: all 0.3s ease;
  z-index: 9999;
}

.toast.show {
  opacity: 1;
  transform: translateX(0);
}

.toast-success {
  background: linear-gradient(135deg, #4caf50, #66bb6a);
  color: white;
}

.toast-error {
  background: linear-gradient(135deg, #f44336, #ef5350);
  color: white;
}

.toast i {
  font-size: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .item-create-page {
    padding: 10px;
  }

  .create-form-wrapper {
    padding: 20px;
  }

  .page-title {
    font-size: 24px;
  }

  .form-actions {
    flex-direction: column;
  }

  .btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
