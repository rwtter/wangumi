<template>
  <div class="episode-comment-list">
    <!-- 评论统计和过滤器 -->
    <div v-if="comments && comments.length > 0" class="list-header">
      <div class="stats">
        <span class="total-comments">
          <i class="fas fa-comments"></i>
          共 {{ totalComments }} 条评论
        </span>
        <span class="average-rating" v-if="averageRating">
          <i class="fas fa-star"></i>
          平均评分: {{ averageRating.toFixed(1) }}
        </span>
      </div>

      <!-- 排序选择器 -->
      <div class="sort-selector">
        <label>排序:</label>
        <select v-model="sortBy" @change="handleSortChange">
          <option value="time_desc">最新优先</option>
          <option value="time_asc">最早优先</option>
          <option value="likes_desc">最多点赞</option>
        </select>
      </div>
    </div>

    <!-- 评论列表 -->
    <div v-if="comments && comments.length > 0" class="comments-container">
      <div
        v-for="comment in comments"
        :key="comment.comment_id"
        class="comment-item"
      >
        <!-- 评论主体 -->
        <div class="comment-main">
          <img
            :src="getCommentAvatar(comment.author)"
            :alt="comment.author?.username"
            class="comment-avatar"
          />

          <div class="comment-content">
            <!-- 评论头部信息 -->
            <div class="comment-header-info">
              <span class="comment-user">{{ comment.author?.username || '匿名用户' }}</span>

              <!-- 显示评分 -->
              <div class="comment-rating" v-if="comment.score">
                <StarRating :modelValue="comment.score" :readonly="true" />
              </div>

              <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
            </div>

            <!-- 评论文本 -->
            <p class="comment-text">
              {{ comment.content }}
            </p>

            <!-- 评论操作 -->
            <div class="comment-actions">
              <button
                class="action-btn like-btn"
                :class="{ liked: comment.is_liked }"
                @click="handleLike(comment)"
              >
                <i class="fas fa-heart"></i>
                <span>{{ comment.likes_count || 0 }}</span>
              </button>

              <button
                class="action-btn reply-btn"
                @click="toggleReplyForm(comment)"
              >
                <i class="fas fa-reply"></i>
                <span>回复 ({{ comment.replies_count || 0 }})</span>
              </button>

              <!-- 展开/收起回复按钮 -->
              <button
                v-if="(comment.replies_count || 0) > 0"
                class="action-btn expand-btn"
                @click="toggleReplies(comment)"
              >
                <i
                  class="fas"
                  :class="
                    expandedComments.includes(comment.comment_id)
                      ? 'fa-chevron-up'
                      : 'fa-chevron-down'
                  "
                ></i>
                <span>{{
                  expandedComments.includes(comment.comment_id)
                    ? '收起'
                    : '查看回复'
                }}</span>
              </button>

              <!-- 举报按钮 -->
              <button
                class="action-btn report-btn"
                @click="handleReport(comment)"
              >
                <i class="fas fa-flag"></i>
                <span>举报</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 回复表单 -->
        <div
          v-if="replyingTo === comment.comment_id"
          class="reply-form"
        >
          <textarea
            v-model="replyContent"
            placeholder="写下你的回复..."
            class="reply-input"
            maxlength="500"
            @keydown.enter.ctrl="submitReply(comment)"
          ></textarea>
          <div class="reply-form-footer">
            <span class="reply-hint">Ctrl + Enter 快速发送</span>
            <div class="reply-actions">
              <button
                @click="submitReply(comment)"
                class="submit-reply"
                :disabled="isSubmittingReply"
                :class="{ submitting: isSubmittingReply }"
              >
                <i class="fas" :class="isSubmittingReply ? 'fa-spinner fa-spin' : 'fa-paper-plane'"></i>
                {{ isSubmittingReply ? '提交中...' : '发布回复' }}
              </button>
              <button
                @click="cancelReply"
                class="cancel-reply"
                :disabled="isSubmittingReply"
              >
                <i class="fas fa-times"></i>
                取消
              </button>
            </div>
          </div>
        </div>

        <!-- 回复列表 -->
        <div
          v-if="expandedComments.includes(comment.comment_id) && loadingReplies[comment.comment_id]"
          class="loading-replies"
        >
          <i class="fas fa-spinner fa-spin"></i>
          <span>加载回复中...</span>
        </div>

        <div
          v-else-if="
            expandedComments.includes(comment.comment_id) &&
            commentReplies[comment.comment_id] &&
            commentReplies[comment.comment_id].length > 0
          "
          class="replies-list"
        >
          <div
            v-for="reply in commentReplies[comment.comment_id]"
            :key="reply.reply_id"
            class="reply-item"
          >
            <img
              :src="getCommentAvatar(reply.author)"
              :alt="reply.author?.username"
              class="reply-avatar"
            />
            <div class="reply-content">
              <div class="reply-header">
                <span class="reply-user">{{ reply.author?.username || '匿名用户' }}</span>
                <span class="reply-time">{{ formatTime(reply.created_at) }}</span>
              </div>
              <p class="reply-text">{{ reply.content }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-data">
      <i class="fas fa-comments"></i>
      <p>暂无评论</p>
      <span class="empty-hint">成为第一个评论的人吧！</span>
    </div>

    <!-- 分页 -->
    <div v-if="comments && comments.length > 0 && totalPages > 1" class="pagination">
      <button
        class="page-btn"
        :disabled="currentPage <= 1"
        @click="goToPage(currentPage - 1)"
      >
        <i class="fas fa-chevron-left"></i>
        上一页
      </button>
      <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
      <button
        class="page-btn"
        :disabled="currentPage >= totalPages"
        @click="goToPage(currentPage + 1)"
      >
        下一页
        <i class="fas fa-chevron-right"></i>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import StarRating from './StarRating.vue'
import {
  getEpisodeComments,
  getCommentReplies,
  replyToComment,
  likeComment,
  unlikeComment,
  reportComment
} from '@/services/episodeCommentService.js'

const props = defineProps({
  episodeId: {
    type: [Number, String],
    required: true
  },
  refresh: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['reply-submitted', 'comment-liked', 'page-change'])

// 响应式数据
const comments = ref([])
const totalComments = ref(0)
const averageRating = ref(0)
const currentPage = ref(1)
const totalPages = ref(0)
const sortBy = ref('time_desc')

const replyingTo = ref(null)
const replyContent = ref('')
const isSubmittingReply = ref(false)  // 回复提交状态
const expandedComments = ref([])
const commentReplies = ref({})
const loadingReplies = ref({})

// 获取评论列表
const fetchComments = async (page = 1) => {
  try {
    const response = await getEpisodeComments(props.episodeId, {
      page: page,
      page_size: 20,
      order_by: sortBy.value
    })

    if (response.code === 200 && response.data) {
      comments.value = response.data.comments || []
      totalComments.value = response.data.total_comments || 0
      averageRating.value = response.data.object_info?.average_rating || 0
      currentPage.value = response.data.page || 1
      totalPages.value = response.data.total_pages || 0
    }
  } catch (error) {
    console.error('获取评论列表失败:', error)
    showToast('加载评论失败', 'error')
  }
}

// 处理排序变化
const handleSortChange = () => {
  fetchComments(1)
}

// 切换到指定页
const goToPage = (page) => {
  if (page < 1 || page > totalPages.value) return
  fetchComments(page)
  emit('page-change', page)
}

// 获取评论作者头像
const getCommentAvatar = (author) => {
  if (author?.avatar) {
    return author.avatar
  }
  const initial = author?.username ? author.username.charAt(0).toUpperCase() : 'U'
  return `https://via.placeholder.com/50x50/6ba3d8/ffffff?text=${initial}`
}

// 格式化时间
const formatTime = (timeString) => {
  if (!timeString) return '未知'

  try {
    const date = new Date(timeString)
    const now = new Date()
    const diff = now - date
    const seconds = Math.floor(diff / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (days > 7) {
      return date.toLocaleDateString('zh-CN')
    } else if (days > 0) {
      return `${days}天前`
    } else if (hours > 0) {
      return `${hours}小时前`
    } else if (minutes > 0) {
      return `${minutes}分钟前`
    } else {
      return '刚刚'
    }
  } catch (error) {
    return '未知'
  }
}

// 切换回复表单
const toggleReplyForm = (comment) => {
  // 检查登录状态
  const token = localStorage.getItem('access_token')
  if (!token) {
    showToast('请先登录', 'error')
    return
  }

  if (replyingTo.value === comment.comment_id) {
    replyingTo.value = null
    replyContent.value = ''
  } else {
    replyingTo.value = comment.comment_id
    replyContent.value = ''
  }
}

// 取消回复
const cancelReply = () => {
  replyingTo.value = null
  replyContent.value = ''
}

// 提交回复
const submitReply = async (comment) => {
  if (!replyContent.value.trim()) {
    showToast('请输入回复内容', 'error')
    return
  }

  // 调试：检查评论ID
  console.log('提交回复 - 评论数据:', {
    comment: comment,
    comment_id: comment.comment_id,
    replyContent: replyContent.value.trim()
  })

  // 验证评论ID
  if (!comment || !comment.comment_id) {
    console.error('评论ID缺失:', comment)
    showToast('评论ID缺失，无法回复', 'error')
    return
  }

  // 防止重复提交
  if (isSubmittingReply.value) {
    return
  }

  isSubmittingReply.value = true

  try {
    const response = await replyToComment(comment.comment_id, replyContent.value.trim())

    if (response.code === 201 || response.code === 200) {
      showToast('回复发布成功！', 'success')

      // 触发事件通知父组件
      emit('reply-submitted', {
        commentId: comment.comment_id,
        reply: response.data
      })

      // 关闭回复表单
      cancelReply()

      // 重新加载评论列表
      await fetchComments(currentPage.value)
    } else {
      throw new Error(response.message || '回复失败')
    }
  } catch (error) {
    console.error('提交回复失败:', error)
    showToast(error.response?.data?.message || error.message || '回复失败，请稍后重试', 'error')
  } finally {
    isSubmittingReply.value = false
  }
}

// 切换回复展开/收起
const toggleReplies = async (comment) => {
  const index = expandedComments.value.indexOf(comment.comment_id)

  if (index > -1) {
    // 收起回复
    expandedComments.value.splice(index, 1)
  } else {
    // 展开回复
    expandedComments.value.push(comment.comment_id)

    // 如果还没有加载过回复，则加载
    if (!commentReplies.value[comment.comment_id]) {
      await loadReplies(comment.comment_id)
    }
  }
}

// 加载回复列表
const loadReplies = async (commentId) => {
  loadingReplies.value[commentId] = true

  try {
    const response = await getCommentReplies(commentId, {
      page: 1,
      page_size: 20
    })

    if (response.code === 200 && response.data) {
      commentReplies.value[commentId] = response.data.replies || []
    }
  } catch (error) {
    console.error('获取回复列表失败:', error)
    showToast('加载回复失败', 'error')
  } finally {
    loadingReplies.value[commentId] = false
  }
}

// 点赞评论
const handleLike = async (comment) => {
  // 检查登录状态
  const token = localStorage.getItem('access_token')
  if (!token) {
    showToast('请先登录', 'error')
    return
  }

  try {
    let response
    if (comment.is_liked) {
      // 取消点赞
      response = await unlikeComment(comment.comment_id)
    } else {
      // 点赞
      response = await likeComment(comment.comment_id)
    }

    if (response.code === 200) {
      // 更新本地状态
      comment.is_liked = !comment.is_liked
      comment.likes_count = response.data.likes_count

      // 触发事件通知父组件
      emit('comment-liked', {
        commentId: comment.comment_id,
        liked: comment.is_liked
      })

      showToast(response.message || (comment.is_liked ? '点赞成功' : '取消点赞'), 'success')
    }
  } catch (error) {
    console.error('点赞操作失败:', error)
    showToast(error.response?.data?.message || '操作失败，请稍后重试', 'error')
  }
}

// 举报评论
const handleReport = async (comment) => {
  // 检查登录状态
  const token = localStorage.getItem('access_token')
  if (!token) {
    showToast('请先登录', 'error')
    return
  }

  // 简单的举报确认
  const categories = {
    'SPAM': '垃圾广告',
    'OFFENSIVE': '辱骂攻击',
    'ILLEGAL': '违法内容',
    'OTHER': '其他'
  }

  const category = prompt('请选择举报类型:\n1. 垃圾广告\n2. 辱骂攻击\n3. 违法内容\n4. 其他\n\n请输入数字(1-4):')

  if (!category) return

  const categoryMap = {
    '1': 'SPAM',
    '2': 'OFFENSIVE',
    '3': 'ILLEGAL',
    '4': 'OTHER'
  }

  const selectedCategory = categoryMap[category]
  if (!selectedCategory) {
    showToast('无效的举报类型', 'error')
    return
  }

  const reason = prompt('请简要说明举报原因(可选):') || ''

  try {
    const response = await reportComment(comment.comment_id, selectedCategory, reason)

    if (response.code === 201 || response.code === 200) {
      showToast('举报提交成功', 'success')
    } else {
      throw new Error(response.message || '举报失败')
    }
  } catch (error) {
    console.error('举报失败:', error)
    if (error.response?.status === 400) {
      showToast('你已经举报过该评论', 'error')
    } else {
      showToast(error.response?.data?.message || '举报失败，请稍后重试', 'error')
    }
  }
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

// 监听刷新属性
watch(() => props.refresh, (newVal) => {
  if (newVal) {
    fetchComments(1)
  }
})

// 生命周期
onMounted(() => {
  fetchComments(1)
})
</script>

<style scoped>
.episode-comment-list {
  margin-top: 30px;
}

/* 列表头部 */
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(162, 210, 255, 0.08), rgba(189, 224, 254, 0.08));
  border-radius: 15px;
  border: 2px solid #a2d2ff;
}

.stats {
  display: flex;
  gap: 25px;
  align-items: center;
}

.total-comments,
.average-rating {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
  font-weight: 500;
  font-size: 15px;
}

.total-comments i,
.average-rating i {
  color: #6ba3d8;
}

.sort-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sort-selector label {
  color: #666;
  font-weight: 500;
}

.sort-selector select {
  padding: 8px 15px;
  border: 2px solid #a2d2ff;
  border-radius: 10px;
  background: white;
  color: #666;
  font-family: inherit;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.sort-selector select:hover {
  border-color: #6ba3d8;
}

.sort-selector select:focus {
  outline: none;
  border-color: #6ba3d8;
  box-shadow: 0 0 0 3px rgba(162, 210, 255, 0.2);
}

/* 评论列表 */
.comments-container {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.comment-item {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  border: 2px solid #a2d2ff;
  padding: 25px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.comment-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(162, 210, 255, 0.2);
}

.comment-main {
  display: flex;
  gap: 20px;
}

.comment-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #6ba3d8;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(107, 163, 216, 0.3);
}

.comment-content {
  flex: 1;
}

.comment-header-info {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
  flex-wrap: wrap;
}

.comment-user {
  color: #333;
  font-weight: 600;
  font-size: 16px;
}

.comment-rating {
  display: flex;
  align-items: center;
}

.comment-time {
  color: #999;
  font-size: 13px;
  margin-left: auto;
}

.comment-text {
  color: #666;
  line-height: 1.8;
  font-size: 14px;
  margin-bottom: 15px;
  padding: 15px;
  background: rgba(162, 210, 255, 0.05);
  border-radius: 12px;
  border-left: 4px solid #6ba3d8;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 评论操作按钮 */
.comment-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.8);
  border: 1.5px solid #a2d2ff;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: inherit;
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

.action-btn:hover {
  background: rgba(162, 210, 255, 0.15);
  border-color: #6ba3d8;
  color: #6ba3d8;
  transform: translateY(-2px);
}

.action-btn i {
  font-size: 13px;
}

.like-btn.liked {
  background: rgba(162, 210, 255, 0.15);
  border-color: #6ba3d8;
  color: #6ba3d8;
}

.like-btn.liked i {
  animation: heartbeat 0.6s ease;
}

@keyframes heartbeat {
  0%, 100% {
    transform: scale(1);
  }
  25% {
    transform: scale(1.3);
  }
  50% {
    transform: scale(1.1);
  }
}

/* 回复表单 */
.reply-form {
  margin-top: 20px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(162, 210, 255, 0.08), rgba(189, 224, 254, 0.08));
  border-radius: 15px;
  border: 2px solid #a2d2ff;
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

.reply-input {
  width: 100%;
  min-height: 90px;
  padding: 12px;
  border: 2px solid #a2d2ff;
  border-radius: 12px;
  resize: vertical;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 12px;
  transition: all 0.3s ease;
}

.reply-input:focus {
  outline: none;
  border-color: #6ba3d8;
  box-shadow: 0 0 0 4px rgba(162, 210, 255, 0.2);
}

.reply-form-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.reply-hint {
  color: #999;
  font-size: 12px;
  font-style: italic;
}

.reply-actions {
  display: flex;
  gap: 10px;
}

.submit-reply,
.cancel-reply {
  padding: 10px 20px;
  border-radius: 20px;
  cursor: pointer;
  font-family: inherit;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  border: none;
  display: flex;
  align-items: center;
  gap: 6px;
}

.submit-reply {
  background: linear-gradient(135deg, #a2d2ff, #bde0fe);
  color: white;
  box-shadow: 0 2px 8px rgba(162, 210, 255, 0.3);
}

.submit-reply:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(162, 210, 255, 0.4);
}

.submit-reply:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.submit-reply.submitting {
  background: linear-gradient(135deg, #8bb8e8, #9fc9ed);
}

.cancel-reply {
  background: rgba(255, 255, 255, 0.9);
  color: #999;
  border: 1.5px solid #e0e0e0;
}

.cancel-reply:hover:not(:disabled) {
  background: #f5f5f5;
  color: #666;
  border-color: #ccc;
}

.cancel-reply:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 加载回复 */
.loading-replies {
  margin-top: 20px;
  padding: 20px;
  text-align: center;
  color: #999;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

/* 回复列表 */
.replies-list {
  margin-top: 20px;
  padding-left: 50px;
  display: flex;
  flex-direction: column;
  gap: 15px;
  animation: slideDown 0.3s ease;
}

.reply-item {
  display: flex;
  gap: 12px;
  padding: 15px;
  background: rgba(162, 210, 255, 0.06);
  border-radius: 12px;
  border-left: 3px solid #a2d2ff;
  transition: all 0.3s ease;
}

.reply-item:hover {
  background: rgba(162, 210, 255, 0.12);
  transform: translateX(5px);
}

.reply-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #a2d2ff;
  flex-shrink: 0;
}

.reply-content {
  flex: 1;
}

.reply-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.reply-user {
  color: #333;
  font-weight: 600;
  font-size: 14px;
}

.reply-time {
  color: #999;
  font-size: 12px;
}

.reply-text {
  color: #666;
  line-height: 1.6;
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 空状态 */
.empty-data {
  text-align: center;
  padding: 80px 30px;
  color: #999;
  background: rgba(162, 210, 255, 0.05);
  border-radius: 20px;
  border: 2px dashed #a2d2ff;
}

.empty-data i {
  font-size: 64px;
  margin-bottom: 20px;
  color: #a2d2ff;
  opacity: 0.6;
}

.empty-data p {
  font-size: 18px;
  margin: 0 0 10px 0;
  font-weight: 500;
  color: #999;
}

.empty-hint {
  font-size: 14px;
  color: #bbb;
  font-style: italic;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 30px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 15px;
}

.page-btn {
  padding: 10px 20px;
  border: 2px solid #a2d2ff;
  border-radius: 20px;
  background: white;
  color: #6ba3d8;
  cursor: pointer;
  font-family: inherit;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-btn:hover:not(:disabled) {
  background: #a2d2ff;
  color: white;
  transform: translateY(-2px);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-info {
  color: #666;
  font-weight: 500;
  font-size: 14px;
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
  .list-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }

  .stats {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .comment-item {
    padding: 20px 15px;
  }

  .comment-main {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .comment-avatar {
    margin: 0 auto;
  }

  .comment-header-info {
    flex-direction: column;
    align-items: center;
    gap: 10px;
  }

  .comment-time {
    margin-left: 0;
  }

  .comment-actions {
    justify-content: center;
  }

  .replies-list {
    padding-left: 20px;
  }

  .reply-form-footer {
    flex-direction: column;
    gap: 10px;
  }

  .reply-actions {
    width: 100%;
  }

  .submit-reply,
  .cancel-reply {
    flex: 1;
  }

  .pagination {
    gap: 10px;
  }

  .page-btn {
    padding: 8px 16px;
    font-size: 13px;
  }
}
</style>
