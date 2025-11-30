<template>
    <div class="anime-detail-page">  
      <!-- 详情内容 -->
      <main class="detail-content" v-if="animeDetail">
        <!-- 顶部信息区 -->
        <div class="anime-header">
          <div class="cover-section">
            <img :src="animeDetail.basic?.cover || 'https://via.placeholder.com/280x400/ff6b9d/ffffff?text=暂无封面'" 
                 :alt="animeDetail.basic?.title" class="detail-cover" />
          </div>
          
          <div class="info-section">
            <h1 class="detail-title">{{ animeDetail.basic?.title }}</h1>
            <p class="japanese-title" v-if="animeDetail.basic?.titleJapanese">
              {{ animeDetail.basic.titleJapanese }}
            </p>
            
            <div class="rating-section">
              <div class="score">
                <span class="score-number">{{ animeDetail.basic?.rating?.toFixed(1) || '0.0' }}</span>
                <div class="stars">
                  <i v-for="n in 5" :key="n" class="fas fa-star" 
                     :class="{ 'active': n <= Math.floor((animeDetail.basic?.rating || 0) / 2) }"></i>
                </div>
                <span class="score-text">综合评分</span>
              </div>
              
              <div class="meta-info">
                <div class="meta-item">
                  <i class="fas fa-tv"></i>
                  <span>状态: {{ animeDetail.meta?.status || '未知' }}</span>
                </div>
                <div class="meta-item">
                  <i class="fas fa-film"></i>
                  <span>集数: {{ animeDetail.meta?.episodes || 0 }}</span>
                </div>
                <div class="meta-item" v-if="animeDetail.meta?.releaseDate">
                  <i class="far fa-calendar"></i>
                  <span>发布日期: {{ formatFullTime(animeDetail.meta.releaseDate) }}</span>
                </div>
              </div>
            </div>
            
            <div class="categories">
              <span 
                v-for="category in animeDetail.meta?.category" 
                :key="category"
                class="category-tag large"
              >
                {{ category }}
              </span>
            </div>
            
            <div class="actions">
              <button class="action-btn favorite" @click="toggleFavorite">
                <i class="fas fa-heart" :class="{ 'active': isFavorite }"></i>
                {{ isFavorite ? '已收藏' : '收藏' }}
              </button>
              <button class="action-btn share" @click="shareAnime">
                <i class="fas fa-share-alt"></i>
                分享
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
            <!-- 简介标签页 -->
            <div v-if="activeTab === 'intro'" class="tab-panel intro-panel">
              <h3>作品简介</h3>
              <p class="summary-text">{{ animeDetail.basic?.summary || '暂无简介' }}</p>
              
              <div class="detail-grid">
                <div class="detail-item">
                  <span class="label">作品类型:</span>
                  <span class="value">{{ animeDetail.meta?.category?.join(' / ') || '未知' }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">状态:</span>
                  <span class="value">{{ animeDetail.meta?.status || '未知' }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">集数:</span>
                  <span class="value">{{ animeDetail.meta?.episodes || 0 }}</span>
                </div>
                <div class="detail-item" v-if="animeDetail.meta?.releaseDate">
                  <span class="label">发布日期:</span>
                  <span class="value">{{ formatFullTime(animeDetail.meta.releaseDate) }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">更新进度:</span>
                  <span class="value">{{ animeDetail.meta?.updateProgress || '暂无信息' }}</span>
                </div>
              </div>
            </div>

            <!-- 剧集标签页 -->
            <div v-if="activeTab === 'episodes'" class="tab-panel episodes-panel">
              <h3>剧集列表</h3>
              <div class="episodes-grid">
                <div
                  v-for="episode in episodes"
                  :key="episode.id"
                  class="episode-card"
                  @click="goToEpisode(episode)"
                >
                  <div class="episode-number">EP {{ episode.number }}</div>
                  <div class="episode-info">
                    <h4>{{ episode.title || `第 ${episode.number} 集` }}</h4>
                    <p v-if="episode.air_date" class="air-date">
                      <i class="fas fa-calendar-alt"></i>
                      {{ formatFullTime(episode.air_date) }}
                    </p>
                    <p v-else class="no-date">点击查看详情</p>
                  </div>
                  <div class="episode-action">
                    <i class="fas fa-play-circle"></i>
                  </div>
                </div>
              </div>

              <!-- 空状态 -->
              <div v-if="episodes.length === 0" class="empty-data">
                <i class="fas fa-film"></i>
                <p>暂无剧集信息</p>
              </div>
            </div>

            <!-- 角色标签页 -->
            <div v-if="activeTab === 'characters'" class="tab-panel characters-panel">
              <h3>角色与制作人员</h3>
              <div v-if="animeDetail.relations?.characters?.length > 0">
                <h4>角色</h4>
                <div class="characters-grid">
                  <div 
                    v-for="character in animeDetail.relations.characters" 
                    :key="character.id"
                    class="character-card"
                  >
                    <img :src="character.avatar" :alt="character.name" class="character-avatar" />
                    <div class="character-info">
                      <h4>{{ character.name }}</h4>
                      <p>{{ character.role }}</p>
                      <span class="cv">CV: {{ character.cv }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div v-if="animeDetail.relations?.staff?.length > 0">
                <h4>制作人员</h4>
                <div class="staff-list">
                  <div 
                    v-for="staff in animeDetail.relations.staff" 
                    :key="staff.id"
                    class="staff-item"
                  >
                    <span class="staff-name">{{ staff.name }}</span>
                    <span class="staff-role">{{ staff.role }}</span>
                  </div>
                </div>
              </div>
              <div v-if="!animeDetail.relations?.characters?.length && !animeDetail.relations?.staff?.length" class="empty-data">
                <i class="fas fa-users"></i>
                <p>暂无角色和制作人员信息</p>
              </div>
            </div>
            
            <!-- 评论标签页 - 使用新的评价组件 -->
            <div v-if="activeTab === 'comments'" class="tab-panel comments-panel">
              <h3>用户评价</h3>

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
                <!-- 评价表单组件 -->
                <ReviewForm
                  :animeId="animeId"
                  @review-submitted="handleReviewSubmitted"
                  @review-updated="handleReviewUpdated"
                />

                <!-- 评价列表组件 -->
                <ReviewList
                  :reviews="comments"
                  @reply-submitted="handleReplySubmitted"
                  @review-liked="handleReviewLiked"
                />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </template>
  


  <script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getAnimeDetail } from '@/services/animeService.js'
import { getComments } from '@/services/commentService.js'
import ReviewForm from './ReviewForm.vue'
import ReviewList from './ReviewList.vue'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const error = ref('')
const animeDetail = ref(null)
const isFavorite = ref(false)
const activeTab = ref('intro')

// 评论相关数据
const comments = ref([])
const commentsLoading = ref(false)
const commentsError = ref('')

// 标签页配置
const tabs = ref([
  { id: 'intro', label: '简介', icon: 'fas fa-info-circle' },
  { id: 'episodes', label: '剧集', icon: 'fas fa-film' },
  { id: 'characters', label: '角色', icon: 'fas fa-users' },
  { id: 'comments', label: '评论', icon: 'fas fa-comments' }
])

// 生成示例剧集数据(实际应该从后端获取)
const episodes = ref([])
const generateEpisodes = () => {
  const totalEpisodes = animeDetail.value?.meta?.episodes || 12
  episodes.value = Array.from({ length: totalEpisodes }, (_, i) => ({
    id: i + 1,
    number: i + 1,
    title: `第 ${i + 1} 集`,
    air_date: null
  }))
}

// 计算属性
const animeId = computed(() => route.params.id)

// 方法
const fetchAnimeDetail = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await getAnimeDetail(animeId.value)

    if (response?.code === 0 && response.data) {
      animeDetail.value = response.data
      // 生成剧集列表
      generateEpisodes()
    } else {
      throw new Error(response?.message || '番剧不存在')
    }

  } catch (err) {
    error.value = err.message || '加载失败，请稍后重试'
    console.error('加载番剧详情失败:', err)
  } finally {
    loading.value = false
  }
}

// 获取评论列表
const fetchComments = async () => {
  commentsLoading.value = true
  commentsError.value = ''

  try {
    const response = await getComments('ANIME', animeId.value, {
      page: 1,
      pageSize: 20,
      orderBy: 'time_desc'
    })

    if (response?.code === 200 && response.data) {
      // 标准化评论数据结构，确保前端组件能正确识别字段
      const rawComments = response.data.comments || []
      comments.value = rawComments.map(comment => ({
        // 保持原有字段
        ...comment,
        // 确保ID字段的一致性 - 后端返回comment_id，前端组件期待多种格式
        reviewId: comment.comment_id,
        // 确保点赞相关字段正确映射
        likes: comment.likes_count || 0,
        isLiked: comment.is_liked || false,
        // 确保用户信息正确映射
        user: comment.author?.username || '匿名用户',
        // 确保评分字段映射
        score: comment.score,
        // 确保内容字段映射
        content: comment.content,
        // 确保时间字段映射
        createdAt: comment.created_at,
        // 确保回复数量字段映射
        replyCount: comment.replies_count || 0
      }))
      console.log('标准化后的评论数据:', comments.value)
    } else {
      throw new Error(response?.message || '获取评论失败')
    }
  } catch (err) {
    commentsError.value = err.message || '加载评论失败，请稍后重试'
    console.error('加载评论失败:', err)
  } finally {
    commentsLoading.value = false
  }
}

// 跳转到单集详情页
const goToEpisode = (episode) => {
  router.push({
    path: `/episode/${episode.id}`,
    query: {
      animeId: animeId.value,
      episodeNumber: episode.number
    }
  })
}

// 格式化方法保持不变
const formatPopularity = (popularity) => {
  if (!popularity) return '0'
  if (popularity >= 10000) {
    return (popularity / 10000).toFixed(1) + '万'
  }
  return popularity.toString()
}

const formatTime = (timeString) => {
  if (!timeString) return '未知'
  return new Date(timeString).getFullYear().toString()
}

const formatFullTime = (timeString) => {
  if (!timeString) return '未知'
  return new Date(timeString).toLocaleDateString('zh-CN')
}

const toggleFavorite = () => {
  isFavorite.value = !isFavorite.value
}

const shareAnime = () => {
  alert('分享功能开发中...')
}

const playAnime = () => {
  alert('播放功能开发中...')
}

// 处理评价提交事件
const handleReviewSubmitted = async (data) => {
  console.log('评价已提交:', data)
  // 重新加载评论列表
  await fetchComments()
}

// 处理评价更新事件
const handleReviewUpdated = async (data) => {
  console.log('评价已更新:', data)
  // 重新加载评论列表
  await fetchComments()
}

// 处理回复提交事件
const handleReplySubmitted = async (data) => {
  console.log('回复已提交:', data)
  // 重新加载评论列表
  await fetchComments()
}

// 处理点赞事件
const handleReviewLiked = async (data) => {
  console.log('评价已点赞:', data)
  // 可以选择重新加载或者只更新本地状态
  // 这里不需要重新加载，因为ReviewList组件已经更新了本地状态
}

// 监听标签页切换
const handleTabChange = (tabId) => {
  activeTab.value = tabId
  // 当切换到评论标签页时，自动加载评论
  if (tabId === 'comments') {
    fetchComments()
  }
}

const goBack = () => {
  router.back()
}

const goHome = () => {
  router.push('/')
}

const handleLogin = () => {
  alert('登录功能开发中...')
}

// 生命周期
onMounted(() => {
  fetchAnimeDetail()
})
</script>

<style scoped>
.anime-detail-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #ffcfe6, #c2e9fb);
  font-family: 'Mochiy Pop One', 'Arial Rounded MT Bold', sans-serif;
  padding: 20px;
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
.anime-header {
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
  justify-content: space-between;
}

.detail-title {
  color: #333;
  font-size: 36px;
  margin-bottom: 10px;
  text-shadow: 2px 2px 0 #ffc2d9;
  line-height: 1.2;
}

.japanese-title {
  color: #666;
  font-size: 18px;
  font-style: italic;
  margin-bottom: 25px;
  border-left: 4px solid #ff6b9d;
  padding-left: 15px;
}

/* 评分区域 */
.rating-section {
  display: flex;
  gap: 50px;
  align-items: flex-start;
  margin-bottom: 25px;
}

.score {
  text-align: center;
  background: rgba(255, 255, 255, 0.8);
  padding: 20px;
  border-radius: 20px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
  border: 2px solid #ffc2d9;
}

.score-number {
  display: block;
  font-size: 42px;
  font-weight: bold;
  color: #ff6b9d;
  text-shadow: 2px 2px 0 #ffc2d9;
}

.stars {
  margin: 12px 0;
  display: flex;
  justify-content: center;
  gap: 4px;
}

.stars i {
  color: #ddd;
  font-size: 18px;
  transition: color 0.3s ease;
}

.stars i.active {
  color: #ffd166;
  text-shadow: 0 0 8px rgba(255, 209, 102, 0.6);
}

.score-text {
  color: #666;
  font-size: 14px;
  font-weight: 500;
}

.meta-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
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
  font-size: 16px;
  font-weight: 500;
}

/* 分类标签 */
.categories {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 30px;
}

.category-tag.large {
  background: linear-gradient(135deg, #a2d2ff, #bde0fe);
  color: white;
  padding: 10px 20px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  border: 2px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 4px 12px rgba(162, 210, 255, 0.3);
  transition: all 0.3s ease;
}

.category-tag.large:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 18px rgba(162, 210, 255, 0.4);
}

/* 操作按钮 */
.actions {
  display: flex;
  gap: 20px;
}

.action-btn {
  padding: 14px 28px;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: inherit;
  font-size: 16px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.action-btn.favorite {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
}

.action-btn.favorite:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 18px rgba(255, 107, 157, 0.4);
}

.action-btn.share {
  background: rgba(255, 255, 255, 0.9);
  color: #ff6b9d;
  border: 2px solid #ffc2d9;
}

.action-btn.share:hover {
  background: rgba(255, 107, 157, 0.1);
  transform: translateY(-3px);
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
  overflow: hidden;
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

.tab-btn:hover::before {
  width: 80%;
}

.tab-btn.active {
  color: #ff6b9d;
  background: rgba(255, 107, 157, 0.1);
}

.tab-btn.active::before {
  width: 100%;
}

.tab-btn i {
  font-size: 18px;
}

.tab-content {
  padding: 40px;
}

/* 简介面板 */
.tab-panel h3 {
  color: #333;
  margin-bottom: 25px;
  font-size: 24px;
  text-shadow: 1px 1px 0 #ffc2d9;
  border-bottom: 3px solid #ffc2d9;
  padding-bottom: 10px;
}

.summary-text {
  line-height: 1.8;
  color: #666;
  margin-bottom: 30px;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.7);
  padding: 20px;
  border-radius: 15px;
  border-left: 4px solid #ff6b9d;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 12px;
  border: 2px solid #ffc2d9;
  transition: all 0.3s ease;
}

.detail-item:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.detail-item .label {
  color: #666;
  font-weight: 500;
}

.detail-item .value {
  color: #333;
  font-weight: 600;
}

/* 剧集面板 */
.episodes-panel h3 {
  color: #333;
  margin-bottom: 25px;
  font-size: 24px;
  text-shadow: 1px 1px 0 #ffc2d9;
  border-bottom: 3px solid #ffc2d9;
  padding-bottom: 10px;
}

.episodes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.episode-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 15px;
  padding: 20px;
  border: 2px solid #a2d2ff;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 15px;
  position: relative;
  overflow: hidden;
}

.episode-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(135deg, #a2d2ff, #bde0fe);
  transform: scaleY(0);
  transform-origin: bottom;
  transition: transform 0.3s ease;
}

.episode-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(162, 210, 255, 0.3);
  border-color: #6ba3d8;
}

.episode-card:hover::before {
  transform: scaleY(1);
}

.episode-number {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #a2d2ff, #bde0fe);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(162, 210, 255, 0.3);
}

.episode-info {
  flex: 1;
  min-width: 0;
}

.episode-info h4 {
  color: #333;
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.episode-info p {
  color: #999;
  margin: 0;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.episode-info .air-date i {
  color: #6ba3d8;
}

.episode-info .no-date {
  color: #bbb;
  font-style: italic;
}

.episode-action {
  color: #6ba3d8;
  font-size: 28px;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.episode-card:hover .episode-action {
  color: #ff6b9d;
  transform: scale(1.1);
}

/* 角色面板 */
.characters-panel h4 {
  color: #ff6b9d;
  margin: 25px 0 15px 0;
  font-size: 20px;
  border-left: 4px solid #a2d2ff;
  padding-left: 15px;
}

.characters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.character-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 20px;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.character-card:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateY(-5px);
  border-color: #ffc2d9;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.character-avatar {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #ff6b9d;
  flex-shrink: 0;
}

.character-info {
  flex: 1;
}

.character-info h4 {
  color: #333;
  margin-bottom: 5px;
  font-size: 16px;
  border: none;
  padding: 0;
}

.character-info p {
  color: #666;
  font-size: 14px;
  margin-bottom: 5px;
}

.cv {
  color: #999;
  font-size: 12px;
  font-style: italic;
}

.staff-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

.staff-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 15px;
  border: 2px solid #a2d2ff;
  transition: all 0.3s ease;
}

.staff-item:hover {
  background: rgba(162, 210, 255, 0.2);
  transform: translateX(5px);
}

.staff-name {
  color: #333;
  font-weight: 500;
}

.staff-role {
  color: #666;
  font-size: 14px;
}

/* 评论面板 - 只保留通用样式 */
.comments-panel {
  /* 评论面板的通用样式由子组件处理 */
}

/* 空状态 */
.empty-data {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.empty-data i {
  font-size: 48px;
  margin-bottom: 15px;
  color: #ffc2d9;
}

.empty-data p {
  font-size: 16px;
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .anime-detail-page {
    padding: 10px;
  }
  
  .anime-header {
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
    font-size: 28px;
  }
  
  .rating-section {
    flex-direction: column;
    gap: 20px;
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
  
  .characters-grid {
    grid-template-columns: 1fr;
  }

  .episodes-grid {
    grid-template-columns: 1fr;
  }

  .comment-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
}

@media (max-width: 480px) {
  .detail-title {
    font-size: 24px;
  }
  
  .tab-btn {
    flex: 1 0 100%;
  }
  
  .character-card {
    flex-direction: column;
    text-align: center;
  }
  
  .character-info {
    text-align: center;
  }
}
</style>
