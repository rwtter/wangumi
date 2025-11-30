<template>
  <div class="episode-detail-page">
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
        <button class="btn btn-retry" @click="fetchEpisodeDetail">
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
    <main class="detail-content" v-else-if="episodeDetail">
      <!-- 顶部信息区 -->
      <div class="episode-header">
        <!-- 返回番剧按钮 -->
        <button class="back-to-anime" @click="goToAnime" v-if="animeId">
          <i class="fas fa-arrow-left"></i>
          返回番剧
        </button>

        <div class="episode-info">
          <div class="episode-badge">
            <i class="fas fa-film"></i>
            第 {{ episodeNumber }} 集
          </div>
          <h1 class="episode-title">{{ episodeDetail.title || `第 ${episodeNumber} 集` }}</h1>
          <p class="episode-subtitle" v-if="episodeDetail.subtitle">
            {{ episodeDetail.subtitle }}
          </p>

          <div class="meta-info">
            <div class="meta-item" v-if="episodeDetail.air_date">
              <i class="fas fa-calendar-alt"></i>
              <span>播出时间: {{ formatDate(episodeDetail.air_date) }}</span>
            </div>
            <div class="meta-item" v-if="episodeDetail.duration">
              <i class="fas fa-clock"></i>
              <span>时长: {{ episodeDetail.duration }} 分钟</span>
            </div>
            <div class="meta-item">
              <i class="fas fa-eye"></i>
              <span>浏览: {{ formatNumber(episodeDetail.view_count || 0) }}</span>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="actions">
            <button class="action-btn play" @click="playEpisode">
              <i class="fas fa-play"></i>
              播放
            </button>
            <button class="action-btn share" @click="shareEpisode">
              <i class="fas fa-share-alt"></i>
              分享
            </button>
          </div>
        </div>

        <!-- 单集封面(如果有) -->
        <div class="episode-cover" v-if="episodeDetail.thumbnail">
          <img :src="episodeDetail.thumbnail" :alt="episodeDetail.title" />
        </div>
      </div>

      <!-- 单集简介 -->
      <div class="episode-description" v-if="episodeDetail.description">
        <h3>
          <i class="fas fa-align-left"></i>
          剧集简介
        </h3>
        <p>{{ episodeDetail.description }}</p>
      </div>

      <!-- 评论区域 -->
      <div class="episode-comments">
        <h3>
          <i class="fas fa-comments"></i>
          单集评论
        </h3>

        <!-- 评论表单组件 -->
        <EpisodeCommentForm
          :episodeId="episodeId"
          @comment-submitted="handleCommentSubmitted"
        />

        <!-- 评论列表组件 -->
        <EpisodeCommentList
          :episodeId="episodeId"
          :refresh="refreshComments"
          @reply-submitted="handleReplySubmitted"
          @comment-liked="handleCommentLiked"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import EpisodeCommentForm from './EpisodeCommentForm.vue'
import EpisodeCommentList from './EpisodeCommentList.vue'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const error = ref('')
const episodeDetail = ref(null)
const refreshComments = ref(false)

// 计算属性
const episodeId = computed(() => route.params.episodeId || route.query.episodeId)
const animeId = computed(() => route.params.animeId || route.query.animeId)
const episodeNumber = computed(() => route.params.episodeNumber || route.query.episodeNumber || episodeId.value)

// 获取单集详情
const fetchEpisodeDetail = async () => {
  loading.value = true
  error.value = ''

  try {
    // TODO: 调用后端API获取单集详情
    // const response = await getEpisodeDetail(episodeId.value)

    // 临时模拟数据
    await new Promise(resolve => setTimeout(resolve, 800))

    episodeDetail.value = {
      id: episodeId.value,
      title: `第 ${episodeNumber.value} 集`,
      subtitle: '单集副标题示例',
      description: '这是单集的详细描述。在这里可以介绍本集的主要剧情、看点和精彩瞬间。',
      air_date: '2024-01-15',
      duration: 24,
      view_count: 1520,
      thumbnail: null
    }

  } catch (err) {
    error.value = err.message || '加载失败，请稍后重试'
    console.error('加载单集详情失败:', err)
  } finally {
    loading.value = false
  }
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '未知'
  return new Date(dateString).toLocaleDateString('zh-CN')
}

// 格式化数字
const formatNumber = (num) => {
  if (!num || num === 0) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toString()
}

// 播放单集
const playEpisode = () => {
  showToast('播放功能开发中...', 'info')
}

// 分享单集
const shareEpisode = () => {
  if (navigator.share) {
    navigator.share({
      title: episodeDetail.value?.title || '单集',
      text: '分享一个精彩的单集',
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

// 返回番剧详情页
const goToAnime = () => {
  if (animeId.value) {
    router.push(`/anime/${animeId.value}`)
  } else {
    goBack()
  }
}

// 返回上一页
const goBack = () => {
  router.back()
}

// 处理评论提交
const handleCommentSubmitted = async (data) => {
  console.log('评论已提交:', data)
  showToast('评论发布成功！', 'success')
  // 刷新评论列表
  refreshComments.value = !refreshComments.value
}

// 处理回复提交
const handleReplySubmitted = async (data) => {
  console.log('回复已提交:', data)
}

// 处理点赞
const handleCommentLiked = async (data) => {
  console.log('评论已点赞:', data)
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
  fetchEpisodeDetail()
})
</script>

<style scoped>
.episode-detail-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #c2e9fb, #a1c4fd);
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
  color: #6ba3d8;
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
  background: linear-gradient(135deg, #a2d2ff, #bde0fe);
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
.episode-header {
  position: relative;
  padding: 40px;
  background: linear-gradient(135deg, rgba(162, 210, 255, 0.15), rgba(189, 224, 254, 0.15));
  border-bottom: 3px solid #a2d2ff;
  display: flex;
  gap: 40px;
  align-items: flex-start;
}

.back-to-anime {
  position: absolute;
  top: 20px;
  left: 20px;
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid #a2d2ff;
  border-radius: 20px;
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

.back-to-anime:hover {
  background: #a2d2ff;
  color: white;
  transform: translateX(-5px);
}

.episode-info {
  flex: 1;
  padding-top: 40px;
}

.episode-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #a2d2ff, #bde0fe);
  color: white;
  padding: 8px 20px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(162, 210, 255, 0.3);
  margin-bottom: 15px;
}

.episode-title {
  color: #333;
  font-size: 32px;
  margin-bottom: 10px;
  text-shadow: 2px 2px 0 #a2d2ff;
  line-height: 1.2;
}

.episode-subtitle {
  color: #666;
  font-size: 16px;
  font-style: italic;
  margin-bottom: 25px;
  padding-left: 15px;
  border-left: 4px solid #6ba3d8;
}

/* 元信息 */
.meta-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 25px;
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
  color: #6ba3d8;
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

.action-btn.play {
  background: linear-gradient(135deg, #a2d2ff, #bde0fe);
  color: white;
}

.action-btn.share {
  background: rgba(255, 255, 255, 0.9);
  color: #6ba3d8;
  border: 2px solid #a2d2ff;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(162, 210, 255, 0.4);
}

/* 单集封面 */
.episode-cover {
  flex-shrink: 0;
  width: 300px;
  height: 200px;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
  border: 4px solid white;
}

.episode-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.episode-cover:hover img {
  transform: scale(1.05);
}

/* 单集简介 */
.episode-description {
  padding: 40px;
  border-bottom: 3px solid #a2d2ff;
}

.episode-description h3 {
  color: #333;
  margin-bottom: 20px;
  font-size: 22px;
  display: flex;
  align-items: center;
  gap: 12px;
  text-shadow: 1px 1px 0 #a2d2ff;
}

.episode-description h3 i {
  color: #6ba3d8;
}

.episode-description p {
  color: #666;
  line-height: 1.8;
  font-size: 15px;
  padding: 20px;
  background: rgba(162, 210, 255, 0.05);
  border-radius: 15px;
  border-left: 4px solid #6ba3d8;
}

/* 评论区域 */
.episode-comments {
  padding: 40px;
  background: rgba(255, 255, 255, 0.98);
}

.episode-comments h3 {
  color: #333;
  margin-bottom: 30px;
  font-size: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  text-shadow: 1px 1px 0 #a2d2ff;
  border-bottom: 3px solid #a2d2ff;
  padding-bottom: 15px;
}

.episode-comments h3 i {
  color: #6ba3d8;
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
  .episode-detail-page {
    padding: 10px;
  }

  .episode-header {
    flex-direction: column;
    padding: 60px 20px 20px;
  }

  .episode-info {
    padding-top: 0;
    text-align: center;
  }

  .episode-badge {
    margin: 0 auto 15px;
  }

  .episode-title {
    font-size: 24px;
  }

  .actions {
    justify-content: center;
  }

  .episode-cover {
    width: 100%;
    height: auto;
    aspect-ratio: 16/9;
    margin: 0 auto;
  }

  .episode-description {
    padding: 20px;
  }

  .episode-comments {
    padding: 20px;
  }
}
</style>
