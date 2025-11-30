<template>
  <div class="review-form">
    <!-- 已登录用户的评价表单 -->
    <div v-if="isLoggedIn" class="form-content">
      <div class="review-header">
        <h4>发表你的评价</h4>
        <p class="hint" v-if="existingReview">你已经评价过这部番剧，可以修改你的评价</p>
      </div>

      <!-- 评分区域 -->
      <div class="rating-input-section">
        <label class="label-text">你的评分：</label>
        <StarRating v-model="localRating" />
      </div>

      <!-- 评论区域 -->
      <div class="comment-section">
        <label class="checkbox-label">
          <input type="checkbox" v-model="wantsToComment" />
          <span>添加评论内容</span>
        </label>

        <div v-if="wantsToComment" class="comment-input-wrapper">
          <textarea
            v-model="localContent"
            placeholder="分享你的观后感...&#10;&#10;例如：&#10;- 剧情紧凑，节奏很好&#10;- 人物塑造很立体&#10;- 画面精美，配乐动听"
            class="review-input"
            maxlength="500"
          ></textarea>
          <div class="char-count">
            <span :class="{ 'near-limit': localContent.length > 450 }">
              {{ localContent.length }} / 500
            </span>
          </div>
        </div>
      </div>

      <!-- 提交按钮 -->
      <div class="form-actions">
        <button
          class="submit-review"
          @click="handleSubmit"
          :disabled="!localRating || isSubmitting"
        >
          <i class="fas fa-paper-plane"></i>
          <span v-if="!isSubmitting">{{ existingReview ? '更新评价' : '发布评价' }}</span>
          <span v-else>提交中...</span>
        </button>

        <button
          v-if="existingReview"
          class="clear-btn"
          @click="handleClear"
          :disabled="isSubmitting"
        >
          <i class="fas fa-times"></i>
          清空表单
        </button>
      </div>
    </div>

    <!-- 未登录提示 -->
    <div v-else class="login-prompt">
      <i class="fas fa-lock"></i>
      <p>请先登录后再发表评价</p>
      <button @click="handleGoToLogin" class="login-btn-inline">
        <i class="fas fa-sign-in-alt"></i>
        去登录
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import StarRating from './StarRating.vue'
import { createAnimeReview, getUserAnimeReview } from '@/services/reviewService.js'
import { createComment } from '@/services/commentService.js'

const props = defineProps({
  animeId: {
    type: [Number, String],
    required: true
  },
  commentType: {
    type: String,
    default: 'ANIME',
    validator: (value) => ['ANIME', 'ITEM', 'EPISODE'].includes(value)
  }
})

const emit = defineEmits(['review-submitted', 'review-updated'])

const router = useRouter()

// 响应式数据
const isLoggedIn = ref(false)
const localRating = ref(0)
const localContent = ref('')
const wantsToComment = ref(false)
const isSubmitting = ref(false)
const existingReview = ref(null)

// 检查登录状态
const checkLoginStatus = () => {
  const token = localStorage.getItem('access_token')
  isLoggedIn.value = !!token
}

// 加载已有评价
const loadExistingReview = async () => {
  if (!isLoggedIn.value) return

  try {
    const response = await getUserAnimeReview(props.animeId)

    if (response.code === 200 && response.data.hasReview !== false) {
      existingReview.value = response.data
      localRating.value = response.data.rating || 0

      if (response.data.comment) {
        localContent.value = response.data.comment
        wantsToComment.value = true
      }
    }
  } catch (error) {
    console.error('加载评价失败:', error)
    // 404 说明用户还没评价过，这是正常的
    if (error.response?.status !== 404) {
      console.warn('获取评价时出错，但不影响新建评价')
    }
  }
}

// 提交评价
const handleSubmit = async () => {
  if (!localRating.value) {
    alert('请先选择评分')
    return
  }

  if (isSubmitting.value) return

  isSubmitting.value = true

  try {
    const comment = wantsToComment.value ? localContent.value.trim() : ''
    let response

    console.log('评论类型:', props.commentType)
    console.log('评论ID:', props.animeId)
    console.log('评分:', localRating.value)
    console.log('内容:', comment)

    // 根据评论类型选择对应的API
    if (props.commentType === 'ITEM') {
      // 条目评论使用新的API
      response = await createComment('ITEM', parseInt(props.animeId), localRating.value, comment)
    } else {
      // 番剧和单集评论使用原有API
      response = await createAnimeReview(props.animeId, localRating.value, comment)
    }

    console.log('提交响应:', response)

    if (response.code === 200 || response.code === 201) {
      alert(existingReview.value ? '评价更新成功！' : '评价提交成功！')

      // 触发事件通知父组件
      if (existingReview.value) {
        emit('review-updated', response.data)
      } else {
        emit('review-submitted', response.data)
      }

      // 更新 existingReview
      existingReview.value = response.data

      // 不清空表单，保留已提交的内容
    } else {
      throw new Error(response.message || '提交失败')
    }
  } catch (error) {
    console.error('提交评价失败:', error)
    const errorMsg = error.response?.data?.message || error.message || '提交失败，请稍后重试'
    alert(errorMsg)
  } finally {
    isSubmitting.value = false
  }
}

// 清空表单
const handleClear = () => {
  localRating.value = 0
  localContent.value = ''
  wantsToComment.value = false
}

// 跳转到登录页
const handleGoToLogin = () => {
  router.push('/login')
}

// 监听评论复选框，自动聚焦到输入框
watch(wantsToComment, (newVal) => {
  if (newVal) {
    // 等待DOM更新后聚焦
    setTimeout(() => {
      const textarea = document.querySelector('.review-input')
      if (textarea) textarea.focus()
    }, 100)
  }
})

// 生命周期
onMounted(() => {
  checkLoginStatus()
  loadExistingReview()
})
</script>

<style scoped>
.review-form {
  margin-bottom: 40px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.form-content {
  padding: 30px;
  border: 2px solid #ffc2d9;
  border-radius: 20px;
}

.review-header {
  margin-bottom: 25px;
}

.review-header h4 {
  color: #ff6b9d;
  font-size: 20px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.review-header .hint {
  color: #999;
  font-size: 14px;
  margin: 0;
  padding: 10px;
  background: rgba(255, 235, 59, 0.1);
  border-radius: 8px;
  border-left: 3px solid #ffc107;
}

/* 评分区域 */
.rating-input-section {
  margin-bottom: 25px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(255, 107, 157, 0.05), rgba(255, 194, 217, 0.05));
  border-radius: 15px;
  border: 2px dashed #ffc2d9;
}

.label-text {
  display: block;
  margin-bottom: 15px;
  color: #666;
  font-weight: 600;
  font-size: 16px;
}

/* 评论区域 */
.comment-section {
  margin-bottom: 25px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
  color: #666;
  font-weight: 500;
  cursor: pointer;
  user-select: none;
  transition: color 0.3s ease;
}

.checkbox-label:hover {
  color: #ff6b9d;
}

.checkbox-label input[type='checkbox'] {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: #ff6b9d;
}

.comment-input-wrapper {
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.review-input {
  width: 100%;
  min-height: 140px;
  padding: 15px;
  border: 2px solid #ffc2d9;
  border-radius: 15px;
  resize: vertical;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.6;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.9);
}

.review-input:focus {
  outline: none;
  border-color: #ff6b9d;
  box-shadow: 0 0 0 4px rgba(255, 107, 157, 0.1);
  background: white;
}

.review-input::placeholder {
  color: #bbb;
  line-height: 1.8;
}

.char-count {
  text-align: right;
  margin-top: 8px;
  padding-right: 5px;
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

.submit-review,
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

.submit-review {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  box-shadow: 0 4px 15px rgba(255, 107, 157, 0.3);
  flex: 1;
  justify-content: center;
}

.submit-review:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 107, 157, 0.4);
}

.submit-review:active:not(:disabled) {
  transform: translateY(0);
}

.submit-review:disabled {
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
  background: linear-gradient(135deg, rgba(255, 107, 157, 0.05), rgba(162, 210, 255, 0.05));
  border-radius: 20px;
  border: 2px dashed #ffc2d9;
}

.login-prompt i {
  font-size: 56px;
  color: #ff6b9d;
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
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  border: none;
  padding: 14px 32px;
  border-radius: 25px;
  cursor: pointer;
  font-family: inherit;
  font-size: 15px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(255, 107, 157, 0.3);
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.login-btn-inline:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 107, 157, 0.4);
}

.login-btn-inline:active {
  transform: translateY(0);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .form-content {
    padding: 20px;
  }

  .form-actions {
    flex-direction: column;
  }

  .submit-review,
  .clear-btn {
    width: 100%;
  }
}
</style>