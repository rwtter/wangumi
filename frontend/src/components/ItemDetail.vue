<template>
  <div class="item-detail-page">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner">
        <i class="fas fa-spinner fa-spin"></i>
      </div>
      <p>加载中...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">
        <i class="fas fa-exclamation-triangle"></i>
      </div>
      <h3>{{ error }}</h3>
      <div class="error-actions">
        <button class="btn btn-retry" @click="fetchItemDetail">
          <i class="fas fa-redo"></i>
          重试
        </button>
        <button class="btn btn-back" @click="goBack">
          <i class="fas fa-arrow-left"></i>
          返回
        </button>
      </div>
    </div>

    <!-- 详情内容 -->
    <main class="detail-content" v-else-if="itemDetail">
      <!-- 顶部信息区 -->
      <div class="item-header">
        <div class="cover-section">
          <img
            :src="getFullImageUrl(itemDetail.basic?.cover) || 'https://via.placeholder.com/280x400/ff6b9d/ffffff?text=暂无封面'"
            :alt="itemDetail.basic?.title"
            class="detail-cover"
          />
        </div>

        <div class="info-section">
          <div class="title-section">
            <h1 class="detail-title">{{ itemDetail.basic?.title }}</h1>
            <span :class="['item-badge', { 'anime-badge': isAnime }]">
              {{ isAnime ? '番剧' : '条目' }}
            </span>
          </div>

          <div class="creator-info">
            <div class="creator-avatar">
              <i class="fas fa-user"></i>
            </div>
            <div class="creator-text">
              <span class="creator-label">创建者</span>
              <span class="creator-name">{{ itemDetail.creator?.username || '未知用户' }}</span>
            </div>
          </div>

          <div class="meta-info">
            <div class="meta-item">
              <i class="fas fa-calendar-alt"></i>
              <span>创建时间: {{ formatTime(itemDetail.basic?.created_at) }}</span>
            </div>
            <div class="meta-item" v-if="itemDetail.basic?.updated_at !== itemDetail.basic?.created_at">
              <i class="fas fa-edit"></i>
              <span>更新时间: {{ formatTime(itemDetail.basic?.updated_at) }}</span>
            </div>
            <div class="meta-item">
              <i class="fas fa-eye"></i>
              <span>浏览次数: {{ formatNumber(itemDetail.basic?.view_count || 0) }}</span>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="actions">
            <button class="action-btn favorite" @click="toggleFavorite">
              <i class="fas fa-heart" :class="{ 'active': isFavorite }"></i>
              {{ isFavorite ? '已收藏' : '收藏' }}
            </button>
            <button class="action-btn share" @click="shareItem">
              <i class="fas fa-share-alt"></i>
              分享
            </button>
            <!-- 删除按钮(仅创建者可见) -->
            <button
              v-if="canDelete"
              class="action-btn delete"
              @click="confirmDelete"
              :disabled="deleting"
            >
              <i class="fas fa-trash" v-if="!deleting"></i>
              <i class="fas fa-spinner fa-spin" v-else></i>
              {{ deleting ? '删除中...' : '删除' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 详情标签页 -->
      <div class="detail-tabs">
        <div class="tab-nav">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            :class="['tab-btn', { active: activeTab === tab.id }]"
            @click="handleTabChange(tab.id)"
          >
            <i :class="tab.icon"></i>
            {{ tab.label }}
          </button>
        </div>

        <div class="tab-content">
          <!-- 详情标签页 -->
          <div v-if="activeTab === 'details'" class="tab-panel details-panel">
            <h3>条目详情</h3>

            <div class="detail-grid">
              <div class="detail-card">
                <div class="detail-card-header">
                  <i class="fas fa-info-circle"></i>
                  <span>基本信息</span>
                </div>
                <div class="detail-card-body">
                  <div class="detail-item">
                    <span class="label">标题:</span>
                    <span class="value">{{ itemDetail.basic?.title || '未知' }}</span>
                  </div>
                  <div class="detail-item" v-if="itemDetail.basic?.title_cn">
                    <span class="label">中文标题:</span>
                    <span class="value">{{ itemDetail.basic.title_cn }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="label">类型:</span>
                    <span class="value item-type">用户创建条目</span>
                  </div>
                </div>
              </div>

              <div class="detail-card" v-if="itemDetail.basic?.description">
                <div class="detail-card-header">
                  <i class="fas fa-file-text"></i>
                  <span>描述</span>
                </div>
                <div class="detail-card-body">
                  <p class="description-text">{{ itemDetail.basic.description }}</p>
                </div>
              </div>

              <div class="detail-card">
                <div class="detail-card-header">
                  <i class="fas fa-chart-line"></i>
                  <span>统计信息</span>
                </div>
                <div class="detail-card-body">
                  <div class="detail-item">
                    <span class="label">评分:</span>
                    <span class="value">{{ formatRating(itemDetail.basic?.rating) }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="label">人气:</span>
                    <span class="value">{{ formatNumber(itemDetail.basic?.popularity || 0) }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="label">评论数:</span>
                    <span class="value">{{ formatNumber(itemDetail.comments?.total || 0) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 评论标签页 -->
          <div v-if="activeTab === 'comments'" class="tab-panel comments-panel">
            <h3>用户评论</h3>

            <!-- 加载状态 -->
            <div v-if="commentsLoading" class="loading-comments">
              <i class="fas fa-spinner fa-spin"></i>
              <span>加载评论中...</span>
            </div>

            <!-- 错误状态 -->
            <div v-else-if="commentsError" class="error-comments">
              <i class="fas fa-exclamation-triangle"></i>
              <span>{{ commentsError }}</span>
              <button @click="fetchComments" class="retry-btn">重试</button>
            </div>

            <!-- 正常状态 -->
            <div v-else>
              <!-- 调试信息 (临时) -->
              <div class="debug-info" style="background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 8px; font-size: 12px; color: #666;">
                调试信息: 条目ID={{ itemId }}, 评论数量={{ comments.length }}, 加载中={{ commentsLoading }}
              </div>

              <!-- 评论表单组件 -->
              <ReviewForm
                :animeId="itemId"
                :commentType="'ITEM'"
                @review-submitted="handleReviewSubmitted"
                @review-updated="handleReviewUpdated"
              />

              <!-- 评论列表组件 -->
              <ReviewList
                :reviews="comments"
                @reply-submitted="handleReplySubmitted"
                @review-liked="handleReviewLiked"
              />

              <!-- 空状态提示 -->
              <div v-if="comments.length === 0" class="no-comments">
                <i class="fas fa-comments"></i>
                <p>暂无评论，快来发表第一个评论吧！</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getItemDetail, deleteItem, getFullImageUrl } from '@/services/itemService.js'
import { getComments } from '@/services/commentService.js'
import ReviewForm from './ReviewForm.vue'
import ReviewList from './ReviewList.vue'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const error = ref('')
const itemDetail = ref(null)
const isFavorite = ref(false)
const activeTab = ref('details')
const deleting = ref(false)

// 评论相关数据
const comments = ref([])
const commentsLoading = ref(false)
const commentsError = ref('')

// 标签页配置
const tabs = ref([
  { id: 'details', label: '详情', icon: 'fas fa-info-circle' },
  { id: 'comments', label: '评论', icon: 'fas fa-comments' }
])

// 计算属性
const itemId = computed(() => route.params.id)

const isAnime = computed(() => {
  // 根据is_admin字段判断是否为番剧
  return itemDetail.value?.basic?.is_admin === true
})

const canDelete = computed(() => {
  // 检查是否为条目创建者
  const currentUserId = getCurrentUserId()
  const creatorId = itemDetail.value?.creator?.id
  return currentUserId && creatorId && currentUserId === creatorId
})

// 获取当前用户ID
const getCurrentUserId = () => {
  // 从localStorage或其他地方获取当前用户ID
  const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
  return userInfo.id || null
}

// 获取条目详情
const fetchItemDetail = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await getItemDetail(itemId.value)

    if (response?.code === 0 && response.data) {
      itemDetail.value = response.data
    } else {
      throw new Error(response?.message || '条目不存在')
    }

  } catch (err) {
    error.value = err.message || '加载失败，请稍后重试'
    console.error('加载条目详情失败:', err)
  } finally {
    loading.value = false
  }
}

// 格式化时间
const formatTime = (timeString) => {
  if (!timeString) return '未知'
  return new Date(timeString).toLocaleString('zh-CN')
}

// 格式化数字
const formatNumber = (num) => {
  if (!num || num === 0) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toString()
}

// 格式化评分
const formatRating = (rating) => {
  if (!rating) return '暂无评分'
  return rating.toFixed(1) + ' 分'
}

// 收藏/取消收藏
const toggleFavorite = () => {
  isFavorite.value = !isFavorite.value
  // TODO: 调用后端API
  const action = isFavorite.value ? '收藏' : '取消收藏'
  showToast(`${action}成功`, 'success')
}

// 分享条目
const shareItem = () => {
  if (navigator.share) {
    navigator.share({
      title: itemDetail.value?.basic?.title || '条目',
      text: '分享一个有趣的条目',
      url: window.location.href
    }).catch(err => {
      console.log('分享失败:', err)
      copyToClipboard()
    })
  } else {
    copyToClipboard()
  }
}

// 复制链接到剪贴板
const copyToClipboard = () => {
  navigator.clipboard.writeText(window.location.href).then(() => {
    showToast('链接已复制到剪贴板', 'success')
  }).catch(() => {
    showToast('复制失败，请手动复制链接', 'error')
  })
}

// 确认删除
const confirmDelete = () => {
  const title = itemDetail.value?.basic?.title || '此条目'
  if (confirm(`确定要删除"${title}"吗？\n\n删除后将无法恢复。`)) {
    handleDelete()
  }
}

// 处理删除
const handleDelete = async () => {
  deleting.value = true

  try {
    const response = await deleteItem(itemId.value)

    if (response?.code === 0) {
      showToast('条目删除成功', 'success')
      // 延迟跳转到列表页
      setTimeout(() => {
        router.push('/items')
      }, 1500)
    } else {
      throw new Error(response?.message || '删除失败')
    }
  } catch (err) {
    console.error('删除条目失败:', err)
    showToast(err.message || '删除失败，请稍后重试', 'error')
  } finally {
    deleting.value = false
  }
}

// 处理评论相关事件
const handleReviewSubmitted = async (data) => {
  console.log('评论已提交:', data)
  // 重新加载评论列表
  await fetchComments()
  showToast('评论提交成功', 'success')
}

const handleReviewUpdated = async (data) => {
  console.log('评论已更新:', data)
  // 重新加载评论列表
  await fetchComments()
  showToast('评论更新成功', 'success')
}

const handleReplySubmitted = async (data) => {
  console.log('回复已提交:', data)
  // 重新加载评论列表
  await fetchComments()
  showToast('回复提交成功', 'success')
}

const handleReviewLiked = async (data) => {
  console.log('评论已点赞:', data)
}

// 返回上一页
const goBack = () => {
  router.back()
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

// 获取评论列表
const fetchComments = async () => {
  commentsLoading.value = true
  commentsError.value = ''

  try {
    console.log('开始获取条目评论，itemId:', itemId.value, ', type:', typeof itemId.value)

    const response = await getComments('ITEM', parseInt(itemId.value), {
      page: 1,
      pageSize: 20,
      orderBy: 'time_desc'
    })

    console.log('评论API完整响应:', response)

    if (response?.code === 200 && response.data) {
      const rawComments = response.data.comments || []
      console.log('原始评论数据:', rawComments)
      console.log('评论总数:', response.data.total_comments)

      // 标准化评论数据结构，确保前端组件能正确识别字段
      comments.value = rawComments.map(comment => ({
        ...comment,
        reviewId: comment.comment_id,        // 标准化为reviewId
        likes: comment.likes_count || 0,     // 标准化为likes
        isLiked: comment.is_liked || false,  // 标准化为isLiked
        user: comment.author?.username || '匿名用户', // 标准化为user
        score: comment.score,
        content: comment.content,
        createdAt: comment.created_at,
        replyCount: comment.replies_count || 0
      }))

      console.log('标准化后的评论数据:', comments.value)
      console.log('评论列表长度:', comments.value.length)
    } else {
      console.error('评论数据响应不正确:', response)
      throw new Error(response?.message || '获取评论失败')
    }
  } catch (err) {
    console.error('获取条目评论失败:', err)
    console.error('错误详情:', err.response?.data || err.message)
    commentsError.value = err.response?.data?.message || err.message || '加载评论失败，请稍后重试'
  } finally {
    commentsLoading.value = false
  }
}

// 处理标签页切换
const handleTabChange = (tabId) => {
  activeTab.value = tabId

  // 当切换到评论标签页时自动加载评论
  if (tabId === 'comments' && comments.value.length === 0 && !commentsLoading.value) {
    fetchComments()
  }
}

// 生命周期
onMounted(() => {
  fetchItemDetail()
})
</script>

<style scoped>
.item-detail-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #ffcfe6, #c2e9fb);
  font-family: 'Mochiy Pop One', 'Arial Rounded MT Bold', sans-serif;
  padding: 20px;
}

/* 加载和错误状态 */
.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
}

.loading-spinner i {
  font-size: 48px;
  color: #ff6b9d;
  margin-bottom: 20px;
}

.error-icon i {
  font-size: 64px;
  color: #ff4081;
  margin-bottom: 20px;
}

.error-state h3 {
  color: #333;
  margin-bottom: 30px;
  font-size: 24px;
}

.error-actions {
  display: flex;
  gap: 15px;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-family: inherit;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.btn-retry {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
}

.btn-back {
  background: rgba(255, 255, 255, 0.9);
  color: #666;
  border: 2px solid #ddd;
}

.btn:hover {
  transform: translateY(-2px);
}

/* 详情内容 */
.detail-content {
  max-width: 1200px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 25px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

/* 顶部信息区 */
.item-header {
  display: flex;
  gap: 40px;
  padding: 40px;
  background: linear-gradient(135deg, rgba(255, 107, 157, 0.1), rgba(162, 210, 255, 0.1));
  border-bottom: 3px solid #ffc2d9;
}

.cover-section {
  flex-shrink: 0;
}

.detail-cover {
  width: 280px;
  height: 400px;
  object-fit: cover;
  border-radius: 20px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
  border: 4px solid white;
  transition: transform 0.3s ease;
}

.detail-cover:hover {
  transform: scale(1.02);
}

.info-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.title-section {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  flex-wrap: wrap;
}

.detail-title {
  color: #333;
  font-size: 32px;
  margin: 0;
  text-shadow: 2px 2px 0 #ffc2d9;
  line-height: 1.2;
  flex: 1;
}

.item-badge {
  background: linear-gradient(135deg, #a2d2ff, #bde0fe);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(162, 210, 255, 0.3);
}

.anime-badge {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4) !important;
  box-shadow: 0 4px 12px rgba(255, 107, 157, 0.3) !important;
}

/* 创建者信息 */
.creator-info {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 20px;
  border: 2px solid #ffc2d9;
}

.creator-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
}

.creator-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.creator-label {
  color: #666;
  font-size: 14px;
}

.creator-name {
  color: #333;
  font-size: 16px;
  font-weight: 600;
}

/* 元信息 */
.meta-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 15px;
  border: 2px solid #a2d2ff;
  transition: all 0.3s ease;
}

.meta-item:hover {
  background: rgba(162, 210, 255, 0.2);
  transform: translateX(5px);
}

.meta-item i {
  color: #ff6b9d;
  width: 20px;
  text-align: center;
}

.meta-item span {
  color: #333;
  font-size: 14px;
  font-weight: 500;
}

/* 操作按钮 */
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.action-btn {
  padding: 14px 24px;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: inherit;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

.action-btn.favorite {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
}

.action-btn.share {
  background: rgba(255, 255, 255, 0.9);
  color: #ff6b9d;
  border: 2px solid #ffc2d9;
}

.action-btn.delete {
  background: linear-gradient(135deg, #ff4444, #ff6666);
  color: white;
}

.action-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(255, 107, 157, 0.4);
}

.action-btn i.active {
  color: #ff6b9d;
}

/* 标签页样式 */
.detail-tabs {
  background: rgba(255, 255, 255, 0.98);
}

.tab-nav {
  display: flex;
  background: linear-gradient(135deg, rgba(255, 107, 157, 0.1), rgba(162, 210, 255, 0.1));
  border-bottom: 3px solid #ffc2d9;
}

.tab-btn {
  flex: 1;
  padding: 20px;
  border: none;
  background: none;
  color: #666;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
  font-family: inherit;
  font-size: 16px;
  font-weight: 500;
  position: relative;
}

.tab-btn::before {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 0;
  height: 3px;
  background: #ff6b9d;
  transition: all 0.3s ease;
  transform: translateX(-50%);
}

.tab-btn:hover {
  color: #ff6b9d;
  background: rgba(255, 107, 157, 0.05);
}

.tab-btn:hover::before,
.tab-btn.active::before {
  width: 80%;
}

.tab-btn.active {
  color: #ff6b9d;
  background: rgba(255, 107, 157, 0.1);
}

.tab-content {
  padding: 40px;
}

/* 详情面板 */
.tab-panel h3 {
  color: #333;
  margin-bottom: 25px;
  font-size: 24px;
  text-shadow: 1px 1px 0 #ffc2d9;
  border-bottom: 3px solid #ffc2d9;
  padding-bottom: 10px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 25px;
}

.detail-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  border: 2px solid #ffc2d9;
}

.detail-card-header {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  padding: 15px 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
}

.detail-card-body {
  padding: 20px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-item .label {
  color: #666;
  font-weight: 500;
}

.detail-item .value {
  color: #333;
  font-weight: 600;
}

.item-type {
  color: #ff6b9d !important;
}

.description-text {
  line-height: 1.6;
  color: #666;
  margin: 0;
  font-size: 15px;
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

.toast-info {
  background: linear-gradient(135deg, #2196f3, #42a5f5);
  color: white;
}

/* 评论加载和错误状态 */
.loading-comments, .error-comments {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 20px;
  text-align: center;
  color: #666;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 15px;
  border: 2px dashed #ffc2d9;
  margin: 20px 0;
}

.loading-comments i {
  color: #ff6b9d;
  font-size: 20px;
}

.error-comments {
  flex-direction: column;
  color: #ff4081;
}

.error-comments i {
  font-size: 24px;
  margin-bottom: 8px;
}

.retry-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 14px;
  margin-top: 12px;
  transition: all 0.3s ease;
}

.retry-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(255, 107, 157, 0.3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .item-detail-page {
    padding: 10px;
  }

  .item-header {
    flex-direction: column;
    padding: 20px;
    text-align: center;
  }

  .detail-cover {
    width: 200px;
    height: 280px;
    margin: 0 auto;
  }

  .detail-title {
    font-size: 24px;
    text-align: center;
  }

  .actions {
    justify-content: center;
  }

  .tab-nav {
    flex-wrap: wrap;
  }

  .tab-btn {
    flex: 1 0 50%;
    padding: 15px 10px;
    font-size: 14px;
  }

  .tab-content {
    padding: 20px;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
