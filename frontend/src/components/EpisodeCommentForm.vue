<template>
  <div class="episode-comment-form">
    <!-- 已登录用户的评论表单 -->
    <div v-if="isLoggedIn" class="form-content">
      <div class="comment-header">
        <h4>
          <i class="fas fa-comment-dots"></i>
          发表单集评论
        </h4>
        <p class="hint">分享你对这一集的观后感</p>
      </div>

      <!-- 评分区域 -->
      <div class="rating-input-section">
        <label class="label-text">你的评分：</label>
        <StarRating v-model="localRating" />
        <span class="rating-value" v-if="localRating">{{ localRating }} 分</span>
      </div>

      <!-- 评论区域 -->
      <div class="comment-section">
        <label class="label-text">评论内容<span class="required">*</span></label>
        <div class="comment-input-wrapper">
          <textarea
            v-model="localContent"
            placeholder="说说你对这一集的看法吧...&#10;&#10;例如:&#10;- 这一集的剧情转折太惊喜了!&#10;- 战斗场面非常精彩&#10;- 角色的心理刻画很细腻"
            class="comment-input"
            maxlength="500"
            :class="{ 'has-error': showError && !localContent.trim() }"
          ></textarea>
          <div class="input-footer">
            <span class="error-text" v-if="showError && !localContent.trim()">
              <i class="fas fa-exclamation-circle"></i>
              评论内容不能为空
            </span>
            <div class="char-count">
              <span :class="{ 'near-limit': localContent.length > 450 }">
                {{ localContent.length }} / 500
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 提交按钮 -->
      <div class="form-actions">
        <button
          class="submit-comment"
          @click="handleSubmit"
          :disabled="isSubmitting || (!localRating && !localContent.trim())"
        >
          <i class="fas fa-paper-plane" v-if="!isSubmitting"></i>
          <i class="fas fa-spinner fa-spin" v-else></i>
          <span v-if="!isSubmitting">发布评论</span>
          <span v-else>提交中...</span>
        </button>

        <button
          class="clear-btn"
          @click="handleClear"
          :disabled="isSubmitting"
        >
          <i class="fas fa-eraser"></i>
          清空
        </button>
      </div>
    </div>

    <!-- 未登录提示 -->
    <div v-else class="login-prompt">
      <i class="fas fa-lock"></i>
      <p>请先登录后再发表评论</p>
      <button @click="handleGoToLogin" class="login-btn-inline">
        <i class="fas fa-sign-in-alt"></i>
        去登录
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import StarRating from './StarRating.vue'
import { createEpisodeComment } from '@/services/episodeCommentService.js'

const props = defineProps({
  episodeId: {
    type: [Number, String],
    required: true
  }
})

const emit = defineEmits(['comment-submitted'])

const router = useRouter()

// 响应式数据
const isLoggedIn = ref(false)
const localRating = ref(0)
const localContent = ref('')
const isSubmitting = ref(false)
const showError = ref(false)

// 检查登录状态
const checkLoginStatus = () => {
  const token = localStorage.getItem('access_token')
  isLoggedIn.value = !!token
}

// 验证表单
const validateForm = () => {
  // 评论内容必填
  if (!localContent.value.trim()) {
    showError.value = true
    showToast('请输入评论内容', 'error')
    return false
  }

  // 评论内容长度限制
  if (localContent.value.trim().length < 1) {
    showError.value = true
    showToast('评论内容至少1个字符', 'error')
    return false
  }

  if (localContent.value.length > 500) {
    showError.value = true
    showToast('评论内容最多500个字符', 'error')
    return false
  }

  // 评分可选,但如果有,必须在1-10之间
  if (localRating.value && (localRating.value < 1 || localRating.value > 10)) {
    showToast('评分必须在1-10之间', 'error')
    return false
  }

  showError.value = false
  return true
}

// 提交评论
const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }

  if (isSubmitting.value) return

  isSubmitting.value = true

  try {
    const response = await createEpisodeComment(
      props.episodeId,
      localRating.value || 5, // 如果没有评分,默认5分
      localContent.value.trim()
    )

    if (response.code === 201 || response.code === 200) {
      showToast('评论发布成功！', 'success')

      // 触发事件通知父组件
      emit('comment-submitted', response.data)

      // 清空表单
      handleClear()
      showError.value = false
    } else {
      throw new Error(response.message || '提交失败')
    }
  } catch (error) {
    console.error('提交评论失败:', error)
    const errorMsg = error.response?.data?.message || error.message || '提交失败，请稍后重试'
    showToast(errorMsg, 'error')
  } finally {
    isSubmitting.value = false
  }
}

// 清空表单
const handleClear = () => {
  localRating.value = 0
  localContent.value = ''
  showError.value = false
}

// 跳转到登录页
const handleGoToLogin = () => {
  router.push('/login')
}

// 显示提示
const showToast = (message, type = 'info') => {
  const toast = document.createElement('div')
  toast.className = `toast toast-${type}`
  toast.innerHTML = `
    <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
    ${message}
  `
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

// 生命周期
onMounted(() => {
  checkLoginStatus()
})
</script>

<style scoped>
.episode-comment-form {
  margin-bottom: 40px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.form-content {
  padding: 30px;
  border: 2px solid #a2d2ff;
  border-radius: 20px;
}

.comment-header {
  margin-bottom: 25px;
}

.comment-header h4 {
  color: #6ba3d8;
  font-size: 20px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.comment-header .hint {
  color: #999;
  font-size: 14px;
  margin: 0;
  padding-left: 30px;
}

/* 评分区域 */
.rating-input-section {
  margin-bottom: 25px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(162, 210, 255, 0.05), rgba(189, 224, 254, 0.05));
  border-radius: 15px;
  border: 2px dashed #a2d2ff;
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}

.label-text {
  color: #666;
  font-weight: 600;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.required {
  color: #ff4444;
  font-size: 14px;
}

.rating-value {
  color: #6ba3d8;
  font-weight: 600;
  font-size: 18px;
  margin-left: 10px;
}

/* 评论区域 */
.comment-section {
  margin-bottom: 25px;
}

.comment-section .label-text {
  display: block;
  margin-bottom: 15px;
}

.comment-input-wrapper {
  width: 100%;
}

.comment-input {
  width: 100%;
  min-height: 140px;
  padding: 15px;
  border: 2px solid #a2d2ff;
  border-radius: 15px;
  resize: vertical;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.6;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.9);
}

.comment-input:focus {
  outline: none;
  border-color: #6ba3d8;
  box-shadow: 0 0 0 4px rgba(162, 210, 255, 0.2);
  background: white;
}

.comment-input.has-error {
  border-color: #ff4444;
}

.comment-input.has-error:focus {
  box-shadow: 0 0 0 4px rgba(255, 68, 68, 0.2);
}

.comment-input::placeholder {
  color: #bbb;
  line-height: 1.8;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding: 0 5px;
}

.error-text {
  color: #ff4444;
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 5px;
}

.char-count {
  text-align: right;
}

.char-count span {
  color: #999;
  font-size: 12px;
  transition: color 0.3s ease;
}

.char-count .near-limit {
  color: #ff6b9d;
  font-weight: bold;
}

/* 表单操作按钮 */
.form-actions {
  display: flex;
  gap: 15px;
  align-items: center;
}

.submit-comment,
.clear-btn {
  padding: 14px 28px;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  font-family: inherit;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.submit-comment {
  background: linear-gradient(135deg, #a2d2ff, #bde0fe);
  color: white;
  box-shadow: 0 4px 15px rgba(162, 210, 255, 0.3);
  flex: 1;
  justify-content: center;
}

.submit-comment:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(162, 210, 255, 0.4);
}

.submit-comment:active:not(:disabled) {
  transform: translateY(0);
}

.submit-comment:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.clear-btn {
  background: rgba(255, 255, 255, 0.9);
  color: #999;
  border: 2px solid #e0e0e0;
}

.clear-btn:hover:not(:disabled) {
  background: #f5f5f5;
  color: #666;
  border-color: #ccc;
}

/* 未登录提示 */
.login-prompt {
  text-align: center;
  padding: 60px 30px;
  background: linear-gradient(135deg, rgba(162, 210, 255, 0.05), rgba(189, 224, 254, 0.05));
  border-radius: 20px;
  border: 2px dashed #a2d2ff;
}

.login-prompt i {
  font-size: 56px;
  color: #6ba3d8;
  margin-bottom: 20px;
  opacity: 0.8;
}

.login-prompt p {
  color: #666;
  font-size: 16px;
  margin-bottom: 25px;
  font-weight: 500;
}

.login-btn-inline {
  background: linear-gradient(135deg, #a2d2ff, #bde0fe);
  color: white;
  border: none;
  padding: 14px 32px;
  border-radius: 25px;
  cursor: pointer;
  font-family: inherit;
  font-size: 15px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(162, 210, 255, 0.3);
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.login-btn-inline:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(162, 210, 255, 0.4);
}

.login-btn-inline:active {
  transform: translateY(0);
}

/* Toast提示 */
:deep(.toast) {
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

:deep(.toast.show) {
  opacity: 1;
  transform: translateX(0);
}

:deep(.toast-success) {
  background: linear-gradient(135deg, #4caf50, #66bb6a);
  color: white;
}

:deep(.toast-error) {
  background: linear-gradient(135deg, #f44336, #ef5350);
  color: white;
}

:deep(.toast-info) {
  background: linear-gradient(135deg, #2196f3, #42a5f5);
  color: white;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .form-content {
    padding: 20px;
  }

  .rating-input-section {
    flex-direction: column;
    align-items: flex-start;
  }

  .form-actions {
    flex-direction: column;
  }

  .submit-comment,
  .clear-btn {
    width: 100%;
  }
}
</style>
