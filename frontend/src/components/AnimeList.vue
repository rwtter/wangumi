<!-- /src/components/AnimeList.vue -->
<template>
  <div class="anime-list-page">
    <main class="main-content">
      <!-- 页面标题和操作栏 -->
      <div class="page-header">
        <div class="header-left">
          <h2 class="page-main-title">
            <i class="fas fa-tv"></i>
            番剧列表
          </h2>
        </div>
        <div class="header-right">
          <button class="items-btn" @click="goToItems">
            <i class="fas fa-th-large"></i>
            查看用户条目
          </button>
        </div>
      </div>

      <!-- 排序和筛选栏 -->
      <div class="filter-section">
        <div class="sort-options">
          <h3 class="filter-title"><i class="fas fa-sort"></i>排序方式</h3>
          <div class="sort-buttons">
            <button
              v-for="sort in sortOptions" :key="sort.value"
              :class="['sort-btn', { active: currentSort === sort.value }]"
              @click="changeSort(sort.value)">
              {{ sort.label }}
            </button>
          </div>
        </div>

        <div class="category-filter">
          <h3 class="filter-title"><i class="fas fa-filter"></i>分类筛选</h3>
          <div class="category-tags">
            <span
              v-for="category in availableCategories" :key="category"
              :class="['category-tag', { active: selectedCategories.includes(category) }]"
              @click="toggleCategory(category)">
              {{ category }}
            </span>
          </div>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-section">
        <div class="loading-spinner">
          <i class="fas fa-spinner fa-spin"></i>
          <p>正在加载番剧数据...</p>
        </div>
      </div>

      <!-- 番剧列表 -->
      <div v-else class="anime-grid">
        <div v-for="anime in animeList" :key="anime.id"
          class="anime-card"
          @click="viewAnimeDetail(anime.id)"><!-- 详情入口 -->
          <div class="anime-cover">
            <img :src="anime.cover" :alt="anime.title" />
            <div class="anime-rating">
              <i class="fas fa-star"></i>
              {{ anime.rating.toFixed(1) }}
            </div>
            <div class="anime-popularity">
              <i class="fas fa-fire"></i>
              {{ formatPopularity(anime.popularity) }}
            </div>
          </div>
          <div class="anime-info">
            <h3 class="anime-title">{{ anime.title }}</h3>
            <p class="anime-summary">{{ truncateSummary(anime.summary) }}</p>
            <div class="anime-meta">
              <span class="anime-time">
                <i class="far fa-clock"></i>
                {{ formatTime(anime.time) }}
              </span>
            </div>
            <div class="anime-categories">
              <span v-for="cat in anime.category" :key="cat"
                class="category-badge">
                {{ cat }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页控件 -->
      <div v-if="!loading && pagination.total > 0" class="pagination-section">
        <div class="pagination-info">
          显示第 {{ (pagination.page - 1) * pagination.limit + 1 }} - 
          {{ Math.min(pagination.page * pagination.limit, pagination.total) }} 条，
          共 {{ pagination.total }} 条番剧
        </div>
        <div class="pagination-controls">
          <button 
            :disabled="pagination.page <= 1"
            @click="changePage(pagination.page - 1)"
            class="page-btn">
            <i class="fas fa-chevron-left"></i>
            上一页
          </button>
          
          <button 
            v-for="page in visiblePages" 
            :key="page"
            :class="['page-btn', 'number', { active: page === pagination.page }]"
            @click="changePage(page)">
            {{ page }}
          </button>
          
          <button 
            :disabled="pagination.page >= pagination.pages"
            @click="changePage(pagination.page + 1)"
            class="page-btn">
            下一页
            <i class="fas fa-chevron-right"></i>
          </button>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="!loading && animeList.length === 0" class="empty-state">
        <i class="fas fa-tv"></i>
        <h3>暂无番剧数据</h3>
        <p>尝试调整筛选条件或稍后重试</p>
      </div>

      <!-- 错误状态 -->
      <div v-if="error" class="error-state">
        <i class="fas fa-exclamation-triangle"></i>
        <h3>数据加载失败</h3>
        <p>{{ error }}</p>
        <button @click="fetchAnimeList" class="retry-btn">重试</button>
      </div>
    </main>
  </div>
</template>

<script setup >
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { getAnimeList } from '@/services/animeService.js'

// 响应式数据
const loading = ref(false)
const error = ref('')
const currentSort = ref('popularity')
const selectedCategories = ref([])
const animeList = ref([])

const pagination = reactive({
  page: 1,
  limit: 12,
  total: 0,
  pages: 0
})

const availableCategories = ref(['Action', 'Drama', 'Mystery', '恋爱', '喜剧', '战斗', '日常', '悬疑', '治愈'])

const sortOptions = ref([
  { value: 'popularity', label: '按热度', icon: 'fas fa-fire' },
  { value: 'time', label: '按时间', icon: 'far fa-clock' },
  { value: 'rating', label: '按评分', icon: 'fas fa-star' }
])

// 计算属性
const visiblePages = computed(() => {
  const current = pagination.page
  const total = pagination.pages
  
  if (total <= 0) return []
  
  const range = 2
  let start = Math.max(1, current - range)
  let end = Math.min(total, current + range)
  
  if (end - start < 4) {
    if (current <= 3) {
      end = Math.min(5, total)
    } else {
      start = Math.max(1, total - 4)
    }
  }
  
  const pages = []
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})

// 方法
const fetchAnimeList = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await getAnimeList({
      sort: currentSort.value,
      category: selectedCategories.value,
      page: pagination.page,
      limit: pagination.limit,
      is_admin: true, // 只获取番剧数据
    })

    if (response && response.code === 0) {
      animeList.value = Array.isArray(response.data?.list) ? response.data.list : []
      const pg = response.data?.pagination || {}
      pagination.page = Math.max(1, Number(pg.page) || 1)
      pagination.limit = Number(pg.limit) || pagination.limit
      pagination.total = Number(pg.total) || 0
      pagination.pages = Number(pg.pages) || 0
    } else {
      error.value = response?.message || '获取数据失败'
    }
  } catch (err) {
    error.value = '网络请求失败，请检查网络连接'
    console.error('请求失败:', err)
  } finally {
    loading.value = false
  }
}

// 已接入真实接口，模拟接口保留可按需删除

const applySorting = (data, sortType) => {
  const sorted = [...data]
  
  switch (sortType) {
    case 'popularity':
      return sorted.sort((a, b) => b.popularity - a.popularity)
    case 'rating':
      return sorted.sort((a, b) => b.rating - a.rating)
    case 'time':
      return sorted.sort((a, b) => new Date(b.time) - new Date(a.time))
    default:
      return sorted
  }
}

const changeSort = (sortType) => {
  currentSort.value = sortType
  pagination.page = 1
  fetchAnimeList()
}

const toggleCategory = (category) => {
  const index = selectedCategories.value.indexOf(category)
  if (index > -1) {
    selectedCategories.value.splice(index, 1)
  } else {
    selectedCategories.value.push(category)
  }
  // 注意：这里不需要手动调用 fetchAnimeList，watch会处理
}

const changePage = (page) => {
  if (page >= 1 && page <= pagination.pages) {
    pagination.page = page
    fetchAnimeList()
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

// 在 AnimeList.vue 的 script 部分添加
import { useRouter } from 'vue-router'

const router = useRouter()

const viewAnimeDetail = (id) => {
  // 跳转到详情页
  router.push(`/anime/${id}`)
}

// 跳转到用户条目列表
const goToItems = () => {
  router.push('/items')
}
/*
const viewAnimeDetail = (id) => {
  console.log('查看番剧详情:', id)
  this.$router.push(`/anime/${id}`)
}
  */


const formatPopularity = (popularity) => {
  if (popularity >= 10000) {
    return (popularity / 10000).toFixed(1) + '万'
  }
  return popularity.toString()
}

const formatTime = (timeString) => {
  return new Date(timeString).getFullYear().toString()
}

const truncateSummary = (summary, length = 60) => {
  if (!summary) return ''
  if (summary.length <= length) return summary
  return summary.substring(0, length) + '...'
}

// 生命周期
onMounted(() => {
  fetchAnimeList()
})

// 监听器 - 添加防抖
let timeoutId = null
watch(selectedCategories, () => {
  clearTimeout(timeoutId)
  timeoutId = setTimeout(() => {
    pagination.page = 1
    fetchAnimeList()
  }, 300)
}, { deep: true })
</script>

<style scoped>
.anime-list-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #ffcfe6, #c2e9fb);
  font-family: 'Mochiy Pop One', 'Arial Rounded MT Bold', sans-serif;
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  gap: 20px;
  flex-wrap: wrap;
}

.header-left {
  flex: 1;
}

.page-main-title {
  color: #333;
  font-size: 32px;
  text-shadow: 2px 2px 0 #ffc2d9;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-main-title i {
  color: #ff6b9d;
}

.header-right {
  display: flex;
  gap: 15px;
}

.items-btn {
  background: linear-gradient(135deg, #a2d2ff, #bde0fe);
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
  box-shadow: 0 4px 12px rgba(162, 210, 255, 0.3);
}

.items-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 18px rgba(162, 210, 255, 0.5);
  background: linear-gradient(135deg, #8ec5fc, #a2d2ff);
}

.items-btn i {
  font-size: 18px;
}

/* 筛选区域 */
.filter-section {
  background: rgba(255, 255, 255, 0.5);
  border-radius: 20px;
  padding: 15px;
  margin-bottom: 30px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  border: 2px solid #ffc2d9;
}

.filter-title {
  color: #ff6b9d;
  margin-top: 5px;
  margin-bottom: 0px;
  font-size: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.sort-options {
  margin-bottom: 10px;
}

.sort-buttons {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.sort-btn {
  background: rgba(255, 107, 157, 0.1);
  border: 2px solid #ffc2d9;
  color: #ff6b9d;
  padding: 10px 20px;
  border-radius: 25px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: inherit;
}

.sort-btn:hover {
  background: rgba(255, 107, 157, 0.2);
  transform: translateY(-2px);
}

.sort-btn.active {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  border-color: #ff6b9d;
}

.category-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.category-tag {
  background: rgba(255, 255, 255, 0.8);
  border: 2px solid #a2d2ff;
  color: #5a5a5a;
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
}

.category-tag:hover {
  transform: scale(1.05);
  border-color: #ff6b9d;
}

.category-tag.active {
  background: linear-gradient(135deg, #a2d2ff, #bde0fe);
  color: white;
  border-color: #a2d2ff;
}

/* 番剧网格 */
.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 25px;
  margin-bottom: 40px;
}

.anime-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
  border: 2px solid transparent;
}

.anime-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 15px 35px rgba(255, 107, 157, 0.2);
  border-color: #ffc2d9;
}

.anime-cover {
  position: relative;
  height: 200px;
  overflow: hidden;
}

.anime-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.anime-card:hover .anime-cover img {
  transform: scale(1.05);
}

.anime-rating, .anime-popularity {
  position: absolute;
  background: rgba(255, 107, 157, 0.9);
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.anime-rating {
  top: 10px;
  left: 10px;
}

.anime-popularity {
  top: 10px;
  right: 10px;
  background: rgba(255, 165, 0, 0.9);
}

.anime-info {
  padding: 20px;
}

.anime-title {
  color: #333;
  font-size: 16px;
  margin-bottom: 10px;
  line-height: 1.4;
  height: 2.8em;
  overflow: hidden;
  display: -webkit-box;
  -webkit-box-orient: vertical;
}

.anime-summary {
  color: #666;
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 15px;
  height: 4.5em;
  overflow: hidden;
  display: -webkit-box;
  -webkit-box-orient: vertical;
}

.anime-meta {
  margin-bottom: 12px;
}

.anime-time {
  color: #888;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.anime-categories {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.category-badge {
  background: rgba(162, 210, 255, 0.2);
  color: #4a90e2;
  padding: 4px 8px;
  border-radius: 10px;
  font-size: 11px;
  border: 1px solid rgba(162, 210, 255, 0.5);
}

/* 加载状态 */
.loading-section {
  text-align: center;
  padding: 60px 20px;
}

.loading-spinner {
  color: #ff6b9d;
  font-size: 24px;
}

.loading-spinner p {
  margin-top: 15px;
  font-size: 16px;
}

/* 分页 */
.pagination-section {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 20px;
  padding: 25px;
  text-align: center;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.pagination-info {
  color: #666;
  margin-bottom: 20px;
  font-size: 14px;
}

.pagination-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.page-btn {
  background: rgba(255, 255, 255, 0.8);
  border: 2px solid #ffc2d9;
  color: #ff6b9d;
  padding: 10px 16px;
  border-radius: 15px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: inherit;
  min-width: 44px;
}

.page-btn:hover:not(:disabled) {
  background: rgba(255, 107, 157, 0.1);
  transform: translateY(-2px);
}

.page-btn.active {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  border-color: #ff6b9d;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: #666;
}

.empty-state i {
  font-size: 64px;
  color: #ffc2d9;
  margin-bottom: 20px;
}

.empty-state h3 {
  color: #ff6b9d;
  margin-bottom: 10px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .page-main-title {
    font-size: 24px;
    justify-content: center;
  }

  .header-right {
    justify-content: center;
  }

  .items-btn {
    width: 100%;
    justify-content: center;
  }

  .nav-container {
    flex-direction: column;
    gap: 15px;
  }

  .nav-links {
    gap: 15px;
  }

  .anime-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 20px;
  }

  .sort-buttons {
    justify-content: center;
  }

  .category-tags {
    justify-content: center;
  }

  .pagination-controls {
    gap: 5px;
  }

  .page-btn {
    padding: 8px 12px;
    font-size: 14px;
  }
}
</style>
