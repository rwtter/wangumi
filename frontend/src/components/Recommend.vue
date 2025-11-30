<template>
  <div class="recommendation-page">
    <div class="page-header"> 
      <div class="tab-container">
        <button 
          :class="['tab-btn', { active: activeTab === 'anime' }]"
          @click="switchTab('anime')"
        >
          番剧推荐
        </button>
        <button 
          :class="['tab-btn', { active: activeTab === 'social' }]"
          @click="switchTab('social')"
        >
          社交推荐
        </button>
      </div>
    </div>

    <!-- 番剧推荐区 -->
    <div v-show="activeTab === 'anime'" class="content-section">
      <div v-if="animeRecommendations.length > 0" class="anime-grid">
        <div v-for="anime in animeRecommendations" :key="anime.id" class="anime-card">
          <div class="card-image-container">
            <img :src="getImageUrl(anime.cover_url)" alt="anime cover" class="anime-cover">
            <div class="rating-badge">{{ anime.rating }}</div>
          </div>
          <div class="card-content">
            <h3 class="anime-title">{{ anime.title }}</h3>
            <div class="recommendation-tags">
              <span v-if="anime.reason === '好友在追'" class="tag friend-tag">好友在追</span>
              <span v-if="anime.reason === '兴趣相似'" class="tag interest-tag">兴趣推荐</span>
              <span v-if="anime.reason === '热门'" class="tag hot-tag">热门</span>
            </div>
            <button class="detail-btn" @click="goToAnimeDetail(anime.id)">查看详情</button>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">
        <p>暂无番剧推荐</p>
      </div>
      
      <!-- 分页控件 -->
      <div v-if="animeTotalPages > 1" class="pagination">
        <button 
          :disabled="animePage <= 1" 
          @click="changeAnimePage(animePage - 1)"
          class="page-btn"
        >
          上一页
        </button>
        <span class="page-info">{{ animePage }} / {{ animeTotalPages }}</span>
        <button 
          :disabled="animePage >= animeTotalPages" 
          @click="changeAnimePage(animePage + 1)"
          class="page-btn"
        >
          下一页
        </button>
      </div>
    </div>

    <!-- 社交推荐区 -->
    <div v-show="activeTab === 'social'" class="content-section">
      <!-- 条目推荐 -->
      <div v-if="entryRecommendations.length > 0" class="social-section">
        <h3 class="section-title">讨论条目推荐</h3>
        <div class="entry-grid">
          <div v-for="entry in entryRecommendations" :key="entry.id" class="entry-card">
            <div class="card-image-container">
              <img :src="getImageUrl(entry.cover_image)" alt="entry cover" class="entry-cover">
              <div class="popularity-badge">热度: {{ entry.popularity }}</div>
            </div>
            <h4 class="entry-title">{{ entry.title }}</h4>
            <button class="detail-btn" @click="goToEntryDetail(entry.id)">查看详情</button>
          </div>
        </div>
      </div>

      <!-- 同好推荐 -->
      <div v-if="userRecommendations.length > 0" class="social-section">
        <h3 class="section-title">同好推荐</h3>
        <div class="user-grid">
          <div v-for="user in userRecommendations" :key="user.id" class="user-card">
            <div class="user-avatar-container">
              <img :src="getImageUrl(user.avatar)" alt="user avatar" class="user-avatar">
            </div>
            <h4 class="username">{{ user.username }}</h4>
            <p class="mutual-count" v-if="user.mutual_watch_count">
              共同追番: {{ user.mutual_watch_count }}部
            </p>
            <button class="profile-btn" @click="goToUserProfile(user.id)">访问主页</button>
          </div>
        </div>
      </div>

      <div v-if="entryRecommendations.length === 0 && userRecommendations.length === 0" class="empty-state">
        <p>暂无社交推荐</p>
      </div>
      
      <!-- 分页控件 -->
      <div v-if="socialTotalPages > 1" class="pagination">
        <button 
          :disabled="socialPage <= 1" 
          @click="changeSocialPage(socialPage - 1)"
          class="page-btn"
        >
          上一页
        </button>
        <span class="page-info">{{ socialPage }} / {{ socialTotalPages }}</span>
        <button 
          :disabled="socialPage >= socialTotalPages" 
          @click="changeSocialPage(socialPage + 1)"
          class="page-btn"
        >
          下一页
        </button>
      </div>
    </div>

    <!-- 用户信息弹窗 -->
    <div v-if="showUserProfileModal" class="modal-overlay" @click.self="closeUserProfile">
      <div class="modal-content">
        <div class="modal-header">
          <h3>用户主页</h3>
          <button class="close-btn" @click="closeUserProfile">×</button>
        </div>
        
        <div class="modal-body">
          <div class="profile-section">
            <h4>关注列表</h4>
            <div v-if="selectedUserProfile.following.length > 0" class="user-list">
              <div v-for="user in selectedUserProfile.following" :key="user.id" class="user-item">
                <img :src="getImageUrl(user.avatar)" class="small-avatar">
                <span>{{ user.username }}</span>
              </div>
            </div>
            <p v-else class="empty-message">暂无关注</p>
          </div>
          
          <div class="profile-section">
            <h4>粉丝列表</h4>
            <div v-if="selectedUserProfile.followers.length > 0" class="user-list">
              <div v-for="user in selectedUserProfile.followers" :key="user.id" class="user-item">
                <img :src="getImageUrl(user.avatar)" class="small-avatar">
                <span>{{ user.username }}</span>
              </div>
            </div>
            <p v-else class="empty-message">暂无粉丝</p>
          </div>
          
          <div class="profile-section">
            <h4>番剧列表</h4>
            <div v-if="selectedUserProfile.animeList.length > 0" class="anime-list">
              <div v-for="anime in selectedUserProfile.animeList" :key="anime.id" class="anime-item">
                <img :src="getImageUrl(anime.cover)" class="small-cover">
                <span>{{ anime.title }}</span>
              </div>
            </div>
            <p v-else class="empty-message">暂无番剧</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      activeTab: 'anime', // 'anime' 或 'social'
      animeRecommendations: [],
      entryRecommendations: [],
      userRecommendations: [],
      selectedUserProfile: null,
      showUserProfileModal: false,
      
      // 分页相关
      animePage: 1,
      animeTotalPages: 1,
      socialPage: 1,
      socialTotalPages: 1,
    };
  },
  async mounted() {
    await this.loadRecommendations();
  },
  methods: {
    getImageUrl(imagePath) {
      if (!imagePath) return '/static/default-avatar.png'; // 返回默认头像
      // 如果已经是完整URL或以/media开头，直接返回
      if (imagePath.startsWith('http') || imagePath.startsWith('/media')) {
        return imagePath;
      }
      // 否则添加/media前缀
      return `/media${imagePath.startsWith('/') ? imagePath : '/' + imagePath}`;
    },

    switchTab(tab) {
      this.activeTab = tab;
    },
    
    async loadRecommendations() {
      try {
        const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
        const headers = {
          'Content-Type': 'application/json',
        };
        
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }

        // 根据当前选项卡加载对应数据
        if (this.activeTab === 'anime') {
          await this.loadAnimeRecommendations(headers);
        } else {
          await this.loadSocialRecommendations(headers);
        }

      } catch (error) {
        console.error('Error fetching recommendations:', error);
      }
    },
    
    async loadAnimeRecommendations(headers) {
      const animeRes = await fetch(
        `/api/recommend_anime/?page=${this.animePage}&limit=12&source=None`,
        { headers }
      );
      const animeData = await animeRes.json();
      this.animeRecommendations = animeData.results || [];
      this.animeTotalPages = Math.ceil((animeData.count || 0) / 12);
    },
    
    async loadSocialRecommendations(headers) {
      const [entryRes, userRes] = await Promise.all([
        fetch(`/api/recommend_items/?page=${this.socialPage}&limit=12`, { headers }),
        fetch(`/api/recommend_users/?page=${this.socialPage}&limit=12`, { headers })
      ]);

      const entryData = await entryRes.json();
      const userData = await userRes.json();

      this.entryRecommendations = entryData.data ? entryData.data.results : [];
      this.userRecommendations = userData.results || [];

      await this.$nextTick();
      
      // 计算总页数
      const entryCount = entryData.data?.count || 0;
      const userCount = userData.count || 0;
      const maxCount = Math.max(entryCount, userCount);
      this.socialTotalPages = Math.ceil(maxCount / 12);
    },
    
    async changeAnimePage(page) {
      this.animePage = page;
      await this.loadAnimeRecommendations(this.getHeaders());
    },
    
    async changeSocialPage(page) {
      this.socialPage = page;
      await this.loadSocialRecommendations(this.getHeaders());
    },
    
    getHeaders() {
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
      const headers = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      return headers;
    },

    goToAnimeDetail(animeId) {
      this.$router.push(`/anime/${animeId}`); 
    },
    
    goToEntryDetail(entryId) {
      this.$router.push(`/anime/${entryId}`);
    },
    
    goToUserProfile(userId) {
      this.fetchUserProfile(userId);
    },
    
    closeUserProfile() {
      this.showUserProfileModal = false;
      this.selectedUserProfile = null;
    },
    
    async fetchUserProfile(userId) {
      try {
        const headers = this.getHeaders();

        const [followingResponse, followerResponse, animeResponse] = await Promise.all([
          fetch(`/api/personal_homepage_following_list/${userId}?page=1&limit=20`, { headers }),
          fetch(`/api/personal_homepage_follower_list/${userId}?page=1&limit=20`, { headers }),
          fetch(`/api/personal_homepage_anime_list/${userId}?page=1&limit=20`, { headers })
        ]);

        const followingData = await followingResponse.json();
        const followerData = await followerResponse.json();
        const animeData = await animeResponse.json();

        console.log('关注数据:', followingData);
        console.log('粉丝数据:', followerData);
        console.log('番剧数据:', animeData);

        this.selectedUserProfile = {
          following: followingData.results || [],
          followers: followerData.results || [],
          animeList: animeData.results || []
        };

        this.showUserProfileModal = true;

      } catch (error) {
        console.error('获取用户信息失败:', error);
        alert('获取用户信息失败');
      }
    }
  },
  
  watch: {
    activeTab() {
      this.loadRecommendations();
    }
  }
};
</script>

<style scoped>
.recommendation-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
}

.page-header h2 {
  color: #2c3e50;
  font-size: 2.5em;
  margin-bottom: 20px;
  font-weight: 600;
}

.tab-container {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-bottom: 30px;
}

.tab-btn {
  padding: 12px 30px;
  border: none;
  background: #f8f9fa;
  color: #6c757d;
  border-radius: 25px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.tab-btn.active {
  background: linear-gradient(135deg,  #f4b0d8 0%, #e3919f 100%);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.content-section {
  min-height: 400px;
}

.anime-grid, .entry-grid, .user-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.anime-card, .entry-card, .user-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
  transition: all 0.3s ease;
  position: relative;
}

.anime-card:hover, .entry-card:hover, .user-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}

.card-image-container {
  position: relative;
  width: 100%;
  height: 280px;
  overflow: hidden;
}

.anime-cover, .entry-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.anime-card:hover .anime-cover,
.entry-card:hover .entry-cover {
  transform: scale(1.05);
}

.rating-badge, .popularity-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(0,0,0,0.7);
  color: white;
  padding: 5px 10px;
  border-radius: 15px;
  font-size: 12px;
  font-weight: 600;
}

.card-content {
  padding: 15px;
}

.anime-title, .entry-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #2c3e50;
  line-height: 1.4;
  display: -webkit-box;
  display: box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  
  /* 备用方案：不支持 line-clamp 的浏览器 */
  max-height: 2.8em; /* 2行的高度 */
}


.recommendation-tags {
  display: flex;
  gap: 5px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.tag {
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.friend-tag {
  background: #e3f2fd;
  color: #1976d2;
}

.interest-tag {
  background: #f3e5f5;
  color: #e3919f;
}

.hot-tag {
  background: #ffebee;
  color: #c62828;
}

.detail-btn, .profile-btn {
  width: 100%;
  padding: 10px;
  border: none;
  background: linear-gradient(135deg, #f4b0d8 0%,  #e3919f 100%);
  color: white;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}

.detail-btn:hover, .profile-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.user-card {
  text-align: center;
  padding: 20px;
}

.user-avatar-container {
  width: 80px;
  height: 80px;
  margin: 0 auto 15px;
  border-radius: 50%;
  overflow: hidden;
  border: 3px solid #f0f0f0;
}

.user-avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.username {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 8px;
}

.mutual-count {
  font-size: 14px;
  color: #6c757d;
  margin-bottom: 15px;
}

.social-section {
  margin-bottom: 40px;
}

.section-title {
  font-size: 1.5em;
  color: #2c3e50;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e9ecef;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  margin-top: 30px;
}

.page-btn {
  padding: 8px 16px;
  border: 1px solid #dee2e6;
  background: white;
  color: #495057;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.page-btn:hover:not(:disabled) {
  background: #f8f9fa;
  border-color: #adb5bd;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-weight: 500;
  color: #495057;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.modal-content {
  background: white;
  border-radius: 16px;
  max-width: 700px;
  width: 90%;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  animation: modalSlideIn 0.3s ease;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-50px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 25px;
  border-bottom: 1px solid #e9ecef;
  background: linear-gradient(135deg, #f4b0d8 0%,  #e3919f 100%);
  color: white;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.3em;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 28px;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background 0.3s ease;
}

.close-btn:hover {
  background: rgba(255,255,255,0.2);
}

.modal-body {
  padding: 25px;
  max-height: calc(80vh - 80px);
  overflow-y: auto;
}

.profile-section {
  margin-bottom: 25px;
}

.profile-section h4 {
  color: #2c3e50;
  font-size: 1.1em;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 2px solid #f0f0f0;
}

.user-list, .anime-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}

.user-item, .anime-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.user-item:hover, .anime-item:hover {
  background: #e9ecef;
  transform: translateY(-2px);
}

.small-avatar, .small-cover {
  width: 40px;
  height: 40px;
  object-fit: cover;
  border-radius: 6px;
}

.empty-message {
  color: #6c757d;
  font-style: italic;
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6c757d;
}

.empty-state p {
  font-size: 1.1em;
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .anime-grid, .entry-grid, .user-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 15px;
  }
  
  .modal-content {
    width: 95%;
    margin: 20px;
  }
  
  .user-list, .anime-list {
    grid-template-columns: 1fr;
  }
}
</style>
