<template>
  <div class="item-list-page">
    <!-- 页头 -->
    <div class="page-header">
      <h1 class="page-title">
        <i class="fas fa-th-large"></i>
        用户条目
      </h1>
      <button class="create-btn" @click="goToCreate">
        <i class="fas fa-plus-circle"></i>
        创建条目
      </button>
    </div>

    <!-- 搜索和筛选栏 -->
    <div class="filter-section">
      <div class="search-box">
        <i class="fas fa-search"></i>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索条目..."
          @input="handleSearch"
        />
        <button
          v-if="searchQuery"
          class="clear-btn"
          @click="clearSearch"
        >
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div class="filter-controls">
        <select v-model="sortBy" @change="handleFilterChange" class="filter-select">
          <option value="time">最新创建</option>
          <option value="hot">最热门</option>
          <option value="rating">最高评分</option>
        </select>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading && itemList.length === 0" class="loading-state">
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
      <p>{{ error }}</p>
      <button class="retry-btn" @click="fetchItemList">
        <i class="fas fa-redo"></i>
        重试
      </button>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!loading && itemList.length === 0" class="empty-state">
      <div class="empty-icon">
        <i class="fas fa-inbox"></i>
      </div>
      <h3>暂无条目</h3>
      <p>{{ searchQuery ? '没有找到匹配的条目' : '还没有任何条目，快来创建第一个吧！' }}</p>
      <button class="create-btn-large" @click="goToCreate" v-if="!searchQuery">
        <i class="fas fa-plus-circle"></i>
        创建第一个条目
      </button>
    </div>

    <!-- 条目列表 -->
    <div v-else class="item-list">
      <div class="item-grid">
        <div
          v-for="item in itemList"
          :key="item.id"
          class="item-card"
          @click="goToDetail(item.id)"
        >
          <div class="item-cover-wrapper">
            <img
              :src="getFullImageUrl(item.cover) || 'https://via.placeholder.com/300x400/ff6b9d/ffffff?text=暂无封面'"
              :alt="item.title"
              class="item-cover"
            />
            <div class="item-overlay">
              <span class="view-detail">查看详情</span>
            </div>
          </div>

          <div class="item-info">
            <h3 class="item-title" :title="item.title">{{ item.title }}</h3>

            <div class="item-meta">
              <div class="meta-row">
                <span class="rating">
                  <i class="fas fa-star"></i>
                  {{ formatRating(item.rating) }}
                </span>
                <span class="popularity">
                  <i class="fas fa-fire"></i>
                  {{ formatPopularity(item.popularity) }}
                </span>
              </div>
              <div class="meta-row">
                <span class="time">
                  <i class="far fa-clock"></i>
                  {{ formatTime(item.time || item.created_at) }}
                </span>
              </div>
            </div>

            <div class="item-tags" v-if="item.category && item.category.length > 0">
              <span
                v-for="tag in item.category.slice(0, 3)"
                :key="tag"
                class="tag"
              >
                {{ tag }}
              </span>
              <span v-if="item.category.length > 3" class="tag-more">
                +{{ item.category.length - 3 }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 加载更多指示器 -->
      <div v-if="loading" class="loading-more">
        <i class="fas fa-spinner fa-spin"></i>
        <span>加载中...</span>
      </div>

      <!-- 分页 -->
      <div v-if="pagination.pages > 1" class="pagination">
        <button
          class="page-btn"
          :disabled="pagination.page <= 1"
          @click="goToPage(pagination.page - 1)"
        >
          <i class="fas fa-chevron-left"></i>
          上一页
        </button>

        <div class="page-numbers">
          <button
            v-for="page in visiblePages"
            :key="page"
            :class="['page-number', { active: page === pagination.page }]"
            @click="goToPage(page)"
          >
            {{ page }}
          </button>
        </div>

        <button
          class="page-btn"
          :disabled="pagination.page >= pagination.pages"
          @click="goToPage(pagination.page + 1)"
        >
          下一页
          <i class="fas fa-chevron-right"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getItemList, getFullImageUrl } from '@/services/itemService.js'

const router = useRouter()

// 状态管理
const loading = ref(false)
const error = ref('')
const itemList = ref([])
const searchQuery = ref('')
const sortBy = ref('time')

// 分页信息
const pagination = reactive({
  page: 1,
  limit: 20,
  total: 0,
  pages: 0
})

// 计算可见的页码
const visiblePages = computed(() => {
  const current = pagination.page
  const total = pagination.pages
  const delta = 2
  const pages = []

  for (let i = Math.max(1, current - delta); i <= Math.min(total, current + delta); i++) {
    pages.push(i)
  }

  return pages
})

// 获取条目列表
const fetchItemList = async (resetPage = false) => {
  if (resetPage) {
    pagination.page = 1
  }

  loading.value = true
  error.value = ''

  try {
    const params = {
      sort: sortBy.value,
      page: pagination.page,
      limit: pagination.limit,
      // 可以添加搜索参数
      search: searchQuery.value || undefined
    }

    const response = await getItemList(params)

    if (response?.code === 0 && response.data) {
      const data = response.data

      // 提取条目列表
      itemList.value = data.list || data.results || []

      // 更新分页信息
      if (data.pagination) {
        pagination.page = data.pagination.page || 1
        pagination.limit = data.pagination.limit || 20
        pagination.total = data.pagination.total || 0
        pagination.pages = data.pagination.pages || 0
      }
    } else {
      throw new Error(response?.message || '获取列表失败')
    }

  } catch (err) {
    error.value = err.message || '加载失败，请稍后重试'
    console.error('获取条目列表失败:', err)
  } finally {
    loading.value = false
  }
}

// 处理搜索
let searchTimeout = null
const handleSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    fetchItemList(true)
  }, 500)
}

// 清除搜索
const clearSearch = () => {
  searchQuery.value = ''
  fetchItemList(true)
}

// 处理筛选变化
const handleFilterChange = () => {
  fetchItemList(true)
}

// 跳转到指定页
const goToPage = (page) => {
  if (page < 1 || page > pagination.pages) return
  pagination.page = page
  fetchItemList()
  // 滚动到顶部
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// 格式化评分
const formatRating = (rating) => {
  if (!rating) return '暂无评分'
  return rating.toFixed(1)
}

// 格式化人气
const formatPopularity = (popularity) => {
  if (!popularity) return '0'
  if (popularity >= 10000) {
    return (popularity / 10000).toFixed(1) + '万'
  }
  return popularity.toString()
}

// 格式化时间
const formatTime = (timeString) => {
  if (!timeString) return '未知'
  const date = new Date(timeString)
  const now = new Date()
  const diffMs = now - date
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return '今天'
  if (diffDays === 1) return '昨天'
  if (diffDays < 7) return `${diffDays}天前`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}周前`
  if (diffDays < 365) return `${Math.floor(diffDays / 30)}个月前`
  return `${Math.floor(diffDays / 365)}年前`
}

// 跳转到创建页面
const goToCreate = () => {
  // 检查登录状态
  const token = localStorage.getItem('access_token')
  if (!token) {
    alert('请先登录')
    router.push('/login')
    return
  }
  router.push('/items/create')
}

// 跳转到详情页
const goToDetail = (id) => {
  router.push(`/item/${id}`)
}

// 生命周期
onMounted(() => {
  fetchItemList()
})
</script>

<style scoped>
.item-list-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #ffcfe6, #c2e9fb);
  font-family: 'Mochiy Pop One', 'Arial Rounded MT Bold', sans-serif;
  padding: 20px;
}

/* 页头 */
.page-header {
  max-width: 1400px;
  margin: 0 auto 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}

.page-title {
  color: #333;
  font-size: 36px;
  text-shadow: 2px 2px 0 #ffc2d9;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 15px;
}

.page-title i {
  color: #ff6b9d;
}

.create-btn {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  border: none;
  border-radius: 25px;
  padding: 14px 28px;
  cursor: pointer;
  font-family: inherit;
  font-size: 16px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(255, 107, 157, 0.3);
}

.create-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 18px rgba(255, 107, 157, 0.4);
}

/* 搜索和筛选 */
.filter-section {
  max-width: 1400px;
  margin: 0 auto 30px;
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.search-box {
  flex: 1;
  min-width: 300px;
  position: relative;
  display: flex;
  align-items: center;
}

.search-box i.fa-search {
  position: absolute;
  left: 20px;
  color: #ff6b9d;
  font-size: 18px;
}

.search-box input {
  width: 100%;
  padding: 15px 50px 15px 50px;
  border: 2px solid #ffc2d9;
  border-radius: 25px;
  font-family: inherit;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.95);
  transition: all 0.3s ease;
}

.search-box input:focus {
  outline: none;
  border-color: #ff6b9d;
  box-shadow: 0 0 0 4px rgba(255, 107, 157, 0.1);
}

.clear-btn {
  position: absolute;
  right: 15px;
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  font-size: 16px;
  padding: 5px;
  transition: color 0.3s ease;
}

.clear-btn:hover {
  color: #ff6b9d;
}

.filter-controls {
  display: flex;
  gap: 15px;
}

.filter-select {
  padding: 15px 20px;
  border: 2px solid #ffc2d9;
  border-radius: 25px;
  font-family: inherit;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.95);
  cursor: pointer;
  transition: all 0.3s ease;
  color: #333;
}

.filter-select:focus {
  outline: none;
  border-color: #ff6b9d;
  box-shadow: 0 0 0 4px rgba(255, 107, 157, 0.1);
}

/* 加载和错误状态 */
.loading-state,
.error-state,
.empty-state {
  max-width: 1400px;
  margin: 60px auto;
  text-align: center;
  padding: 60px 20px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 25px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
}

.loading-spinner i,
.error-icon i,
.empty-icon i {
  font-size: 64px;
  margin-bottom: 20px;
}

.loading-spinner i {
  color: #ff6b9d;
}

.error-icon i {
  color: #ff4081;
}

.empty-icon i {
  color: #ffc2d9;
}

.empty-state h3 {
  color: #333;
  margin: 20px 0 10px;
  font-size: 24px;
}

.empty-state p {
  color: #666;
  margin-bottom: 30px;
  font-size: 16px;
}

.create-btn-large {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  border: none;
  border-radius: 25px;
  padding: 16px 32px;
  cursor: pointer;
  font-family: inherit;
  font-size: 18px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(255, 107, 157, 0.3);
}

.create-btn-large:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 18px rgba(255, 107, 157, 0.4);
}

.retry-btn {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  border: none;
  border-radius: 20px;
  padding: 12px 24px;
  cursor: pointer;
  font-family: inherit;
  font-size: 16px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.retry-btn:hover {
  transform: translateY(-2px);
}

/* 条目列表 */
.item-list {
  max-width: 1400px;
  margin: 0 auto;
}

.item-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 25px;
  margin-bottom: 40px;
}

/* 条目卡片 */
.item-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  border: 3px solid transparent;
}

.item-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 30px rgba(255, 107, 157, 0.3);
  border-color: #ffc2d9;
}

.item-cover-wrapper {
  position: relative;
  width: 100%;
  padding-top: 133%;
  overflow: hidden;
  background: linear-gradient(135deg, #ffc2d9, #a2d2ff);
}

.item-cover {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.item-card:hover .item-cover {
  transform: scale(1.05);
}

.item-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 107, 157, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.item-card:hover .item-overlay {
  opacity: 1;
}

.view-detail {
  color: white;
  font-size: 16px;
  font-weight: 600;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.item-info {
  padding: 20px;
}

.item-title {
  color: #333;
  font-size: 16px;
  margin: 0 0 15px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
  min-height: 2.8em;
}

.item-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #666;
}

.rating,
.popularity,
.time {
  display: flex;
  align-items: center;
  gap: 5px;
}

.rating i {
  color: #ffd166;
}

.popularity i {
  color: #ff6b9d;
}

.time i {
  color: #a2d2ff;
}

.item-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  background: linear-gradient(135deg, #a2d2ff, #bde0fe);
  color: white;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.tag-more {
  background: rgba(255, 107, 157, 0.2);
  color: #ff6b9d;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  padding: 30px 0;
}

.page-btn {
  background: rgba(255, 255, 255, 0.95);
  border: 2px solid #ffc2d9;
  border-radius: 20px;
  padding: 12px 20px;
  cursor: pointer;
  font-family: inherit;
  font-size: 14px;
  font-weight: 500;
  color: #ff6b9d;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.page-btn:hover:not(:disabled) {
  background: #ff6b9d;
  color: white;
  transform: translateY(-2px);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-numbers {
  display: flex;
  gap: 8px;
}

.page-number {
  background: rgba(255, 255, 255, 0.95);
  border: 2px solid #ffc2d9;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  cursor: pointer;
  font-family: inherit;
  font-size: 14px;
  font-weight: 500;
  color: #ff6b9d;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.page-number:hover {
  background: rgba(255, 107, 157, 0.2);
  transform: scale(1.1);
}

.page-number.active {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  border-color: #ff6b9d;
}

.loading-more {
  text-align: center;
  padding: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #ff6b9d;
  font-size: 16px;
}

.loading-more i {
  font-size: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .page-title {
    font-size: 28px;
    justify-content: center;
  }

  .create-btn {
    justify-content: center;
  }

  .filter-section {
    flex-direction: column;
  }

  .search-box {
    min-width: 100%;
  }

  .item-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 15px;
  }

  .pagination {
    flex-wrap: wrap;
    gap: 10px;
  }

  .page-numbers {
    order: 3;
    width: 100%;
    justify-content: center;
  }
}
</style>
