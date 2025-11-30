<template>
  <div class="personal-space-page">
    <main class="main-content">
      <!-- 第一部分：基本信息栏 -->
      <section class="user-info-card">
        <!-- 头像 -->
        <div class="avatar-section">
          <div 
            class="avatar-container" 
            @click="handleEditAvatar"
            :class="{ editable: isOwnProfile }"
          >
            <img :src="userProfile.avatar" :alt="userProfile.username" class="avatar" />
            <div v-if="isOwnProfile" class="avatar-overlay">
              <i class="fas fa-camera"></i>
              <span>更换头像</span>
            </div>
          </div>
        </div>

        <div class="info-section">
          <!-- 用户名 -->
          <div class="user-header">
            <h1 class="username">{{ userProfile.username }}</h1>
            <button 
              v-if="isOwnProfile"
              type="button" 
              class="edit-btn"
              @click="startEditField('username')"
              title="编辑用户名"
            >
              <i class="fas fa-edit"></i>
            </button>
          </div>

          <!-- 个性签名 -->
          <div class="signature-row">
            <p class="signature">{{ userProfile.signature || '这个人很懒，什么都没有写～' }}</p>
            <button 
              v-if="isOwnProfile"
              type="button"
              class="edit-btn"
              @click="startEditField('signature')"
              title="编辑个性签名"
            >
              <i class="fas fa-edit"></i>
            </button>
          </div>
          <!-- 关注/粉丝/追番数 -->
          <div class="stats-bar">
            <div class="stat-item" @click="switchTab('following')">
              <span class="stat-number">{{ userProfile.followingCount }}</span>
              <span class="stat-label">关注</span>
            </div>
            <div class="stat-item" @click="switchTab('followers')">
              <span class="stat-number">{{ userProfile.followersCount }}</span>
              <span class="stat-label">粉丝</span>
            </div>
            <div class="stat-item" @click="switchTab('anime')">
              <span class="stat-number">{{ userProfile.animeCount }}</span>
              <span class="stat-label">追番</span>
            </div>
          </div>
          <!-- 关注按钮（他人可见） -->
          <div class="action-buttons">
            <button 
              v-if="!isOwnProfile"
              type="button"
              class="follow-btn"
              :class="{ 'is-following': isFollowing }"
              @click="toggleFollowStatus"
            >
              <i class="fas" :class="isFollowing ? 'fa-user-check' : 'fa-user-plus'"></i>
              {{ isFollowing ? '已关注' : '关注' }}
            </button>
            <!-- 隐私设置 -->
            <button 
              v-if="isOwnProfile"
              type="button"
              class="settings-btn"
              @click="showPrivacySettingsModal = true"
            >
              <i class="fas fa-cog"></i>
              隐私设置
            </button>
          </div>
        </div>
      </section>

      <!-- 第二部分：筛选展示栏 -->
      <section class="content-area">
        <!-- 标签导航 -->
        <nav class="content-tabs">
          <button 
            type="button"
            class="tab-btn"
            :class="{ active: activeTab === 'intro' }"
            @click="switchTab('intro')"
          >
            个人介绍
          </button>
          <button 
            type="button"
            class="tab-btn"
            :class="{ active: activeTab === 'following' }"
            @click=handFollowingListTabClick()
          >
            关注
          </button>
          <button 
            type="button"
            class="tab-btn"
            :class="{ active: activeTab === 'followers' }"
            @click=handfollowersListTabClick()
          >
            粉丝
          </button>
          <button 
            type="button"
            class="tab-btn"
            :class="{ active: activeTab === 'anime' }"
            @click=handleanimeListTabClick()
          >
            追番
          </button>
          <button 
            type="button"
            class="tab-btn"
            :class="{ active: activeTab === 'dynamics' }"
            @click=handleDynamicTabClick()
          >
            动态
          </button>
        </nav>

        <!-- 内容展示区域 -->
        <div class="tab-content">
          <!-- 个人介绍标签页 -->
          <div v-show="activeTab === 'intro'" class="tab-pane intro-pane">
            <div class="intro-container">
              <div v-if="isOwnProfile" class="intro-header">
                <h3>个人介绍</h3>
                <button 
                  type="button"
                  class="edit-btn-large"
                  @click="startEditField('introduction')"
                  title="编辑个人介绍"
                >
                  <i class="fas fa-edit"></i> 编辑
                </button>
              </div>

              <div v-if="userProfile.introduction" class="intro-display">
                <div class="markdown-content" v-html="renderMarkdown(userProfile.introduction)"></div>
              </div>
              <!-- 个人介绍为空 -->
              <div v-else class="empty-state">
                <i class="fas fa-inbox"></i>
                <p v-if="isOwnProfile">点击编辑按钮添加你的个人介绍～</p>
                <p v-else>这个人很神秘，什么都没有留下～</p>
              </div>
            </div>
          </div>

          <!-- 关注列表标签页 -->
          <div v-show="activeTab === 'following'" class="tab-pane list-pane">
            <div class="list-container">
              <h3>关注列表 ({{ following.length }})</h3>
              <div v-if="following.length > 0" class="user-list">
                <div v-for="user in following" :key="user.id" class="user-item">
                  <img :src="user.avatar" :alt="user.username" class="user-avatar" />
                  <div class="user-info">
                    <div class="user-name">{{ user.username }}</div>
                    <div class="user-signature">{{ user.signature }}</div>
                  </div>
                  <button v-if="isOwnProfile" type="button" class="action-icon-btn" title="取消关注">
                    <i class="fas fa-times"></i>
                  </button>
                </div>
              </div>
              <div v-else class="empty-state">
                <i class="fas fa-heart-broken"></i>
                <p>还没有关注任何人～</p>
              </div>
            </div>
          </div>

          <!-- 粉丝列表标签页 -->
          <div v-show="activeTab === 'followers'" class="tab-pane list-pane">
            <div class="list-container">
              <h3>粉丝列表 ({{ followers.length }})</h3>
              <div v-if="followers.length > 0" class="user-list">
                <div v-for="user in followers" :key="user.id" class="user-item">
                  <img :src="user.avatar" :alt="user.username" class="user-avatar" />
                  <div class="user-info">
                    <div class="user-name">{{ user.username }}</div>
                    <div class="user-signature">{{ user.signature }}</div>
                  </div>
                  <button v-if="isOwnProfile && !isFollowingUser(user.id)" type="button" class="follow-back-btn">
                    回关
                  </button>
                </div>
              </div>
              <div v-else class="empty-state">
                <i class="fas fa-user-slash"></i>
                <p>还没有粉丝～</p>
              </div>
            </div>
          </div>

          <!-- 追番列表标签页 -->
          <div v-show="activeTab === 'anime'" class="tab-pane list-pane">
            <div class="list-container">
              <h3>追番列表 ({{ animeList.length }})</h3>
              <div v-if="animeList.length > 0" class="anime-list">
                <div v-for="anime in animeList" :key="anime.id" class="anime-item">
                  <div v-if="anime.cover" class="anime-cover">
                    <img :src="anime.cover" :alt="anime.title" />
                  </div>
                  <div class="anime-info">
                    <div class="anime-title">{{ anime.title }}</div>
                    <div class="anime-meta">
                      <span class="status-badge" :class="`status-${anime.watchStatus}`">
                        {{ anime.watchStatusText }}
                      </span>
                      <span v-if="anime.currentEpisode" class="episode-info">
                        {{ anime.currentEpisode }}/{{ anime.totalEpisodes }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="empty-state">
                <i class="fas fa-film"></i>
                <p>还没有追番～</p>
              </div>
            </div>
          </div>

          <!-- 动态时间轴标签页 -->
          <div v-show="activeTab === 'dynamics'" class="tab-pane timeline-pane">
            <div class="timeline-container">
              <h3>动态时间轴</h3>
              
              <!-- 动态过滤标签 -->
              <div class="dynamic-filters">
                <button 
                  type="button"
                  class="filter-btn"
                  :class="{ active: dynamicFilter === 'all' }"
                  @click="dynamicFilter = 'all'"
                >
                  全部
                </button>
                <button 
                  type="button"
                  class="filter-btn"
                  :class="{ active: dynamicFilter === 'entry' }"
                  @click="dynamicFilter = 'entry'"
                >
                  条目创建
                </button>
                <button 
                  type="button"
                  class="filter-btn"
                  :class="{ active: dynamicFilter === 'review' }"
                  @click="dynamicFilter = 'review'"
                >
                  评价发布
                </button>
              </div>

              <!-- 时间轴 -->
              <div v-if="filteredDynamics.length > 0" class="timeline">
                <div v-for="dynamic in filteredDynamics" :key="dynamic.id" class="timeline-item">
                  <div class="timeline-marker" :class="dynamic.type"></div>
                  <div class="timeline-content">
                    <div class="dynamic-header">
                      <div class="user-brief">
                        <img :src="dynamic.userAvatar" :alt="dynamic.username" class="avatar-small" />
                        <span class="username-text">{{ dynamic.username }}</span>
                      </div>
                      <span class="timestamp">{{ formatTime(dynamic.createdAt) }}</span>
                    </div>
                    <div class="dynamic-body">
                      <p v-if="dynamic.type === 'entry'">
                        创建了条目 <strong>{{ dynamic.animeTitle }}</strong>
                      </p>
                      <p v-if="dynamic.type === 'review'">
                        评价了 <strong>{{ dynamic.animeTitle }}</strong>：{{ dynamic.content }}
                      </p>
                    </div>
                    <div class="dynamic-actions">
                      <button type="button" class="action-btn">
                        <i class="fas fa-thumbs-up"></i>
                        {{ dynamic.likes }}
                      </button>
                      <button type="button" class="action-btn">
                        <i class="fas fa-comment"></i>
                        {{ dynamic.comments }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <div v-else class="empty-state">
                <i class="fas fa-wind"></i>
                <p>这里还没有动态～</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- 编辑模态框 -->
    <teleport to="body">
      <div v-if="showEditModal" class="modal-overlay" @click="closeEditModal">
        <div class="modal" @click.stop>
          <div class="modal-header">
            <h3>{{ getEditModalTitle() }}</h3>
            <button type="button" class="close-btn" @click="closeEditModal">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="modal-body">
            <!-- 用户名编辑 -->
            <div v-if="editingField === 'username'" class="edit-form">
              <input 
                v-model="editFormData.username"
                type="text"
                placeholder="请输入用户名"
                maxlength="20"
                class="form-input"
                autofocus
              />
              <div class="char-counter">{{ editFormData.username.length }}/20</div>
            </div>

            <!-- 个性签名编辑 -->
            <div v-if="editingField === 'signature'" class="edit-form">
              <textarea 
                v-model="editFormData.signature"
                placeholder="请输入个性签名"
                maxlength="100"
                class="form-textarea"
                rows="3"
                autofocus
              ></textarea>
              <div class="char-counter">{{ editFormData.signature.length }}/100</div>
            </div>

            <!-- 个人介绍编辑 -->
            <div v-if="editingField === 'introduction'" class="edit-form markdown-editor">
              <div class="editor-tabs">
                <button 
                  type="button"
                  class="editor-tab"
                  :class="{ active: editMode === 'edit' }"
                  @click="editMode = 'edit'"
                >
                  编辑
                </button>
                <button 
                  type="button"
                  class="editor-tab"
                  :class="{ active: editMode === 'preview' }"
                  @click="editMode = 'preview'"
                >
                  预览
                </button>
              </div>

              <div v-if="editMode === 'edit'" class="editor-pane">
                <textarea 
                  v-model="editFormData.introduction"
                  placeholder="支持 Markdown 格式..."
                  class="form-textarea"
                  rows="12"
                  autofocus
                ></textarea>
                <div class="markdown-hint">
                  <i class="fas fa-info-circle"></i>
                  支持 Markdown 格式。<a href="https://commonmark.org/" target="_blank">查看语法</a>
                </div>
              </div>

              <div v-if="editMode === 'preview'" class="preview-pane">
                <div class="markdown-preview" v-html="renderMarkdown(editFormData.introduction)"></div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-cancel" @click="closeEditModal">取消</button>
            <button type="button" class="btn btn-save" @click="saveEdit">保存</button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- 隐私设置模态框 -->
    <teleport to="body">
      <div v-if="showPrivacySettingsModal" class="modal-overlay" @click="showPrivacySettingsModal = false">
        <div class="modal" @click.stop>
          <div class="modal-header">
            <h3>隐私设置</h3>
            <button type="button" class="close-btn" @click="showPrivacySettingsModal = false">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="modal-body">
            <div v-for="setting in privacySettings" :key="setting.key" class="privacy-item">
              <div class="privacy-label">
                <h4>{{ setting.label }}</h4>
                <p>{{ setting.description }}</p>
              </div>
              <select v-model="setting.value" class="privacy-select">
                <option value="public">所有人可见</option>
                <option value="followers">粉丝可见</option>
                <option value="private">仅自己可见</option>
              </select>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-cancel" @click="showPrivacySettingsModal = false">取消</button>
            <button type="button" class="btn btn-save" @click="savePrivacySettings">保存</button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- 头像上传模态框 -->
    <teleport to="body">
      <div v-if="showAvatarUploadModal" class="modal-overlay" @click="closeAvatarUploadModal">
        <div class="modal avatar-upload-modal" @click.stop>
          <div class="modal-header">
            <h3>更换头像</h3>
            <button type="button" class="close-btn" @click="closeAvatarUploadModal">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="modal-body">
            <!-- 文件输入（隐藏） -->
            <input 
              ref="avatarFileInput"
              type="file"
              accept="image/*"
              style="display: none"
              @change="handleFileSelect"
            />

            <div v-if="!avatarPreviewUrl" class="upload-placeholder">
              <i class="fas fa-cloud-upload-alt"></i>
              <p>选择图片进行上传</p>
              <button 
                type="button"
                class="btn-upload"
                @click="avatarFileInput?.click()"
              >
                点击选择图片
              </button>
            </div>

            <div v-else class="crop-container">
              <div class="crop-header">
                <h4>裁剪头像</h4>
                <p>拖动裁剪框调整位置，使用按钮或输入框改变大小</p>
              </div>
              
              <canvas 
                ref="avatarCanvas"
                class="crop-canvas"
                width="500"
                height="500"
                @mousedown="handleCanvasMouseDown"
                @mousemove="handleCanvasMouseMove"
                @mouseup="handleCanvasMouseUp"
                @mouseleave="handleCanvasMouseUp"
              ></canvas>

              <div class="crop-controls">
                <button 
                  type="button"
                  class="size-btn"
                  @click="resizeCropper(-20)"
                  title="缩小裁剪框"
                >
                  <i class="fas fa-minus"></i>
                  缩小
                </button>
                
                <div class="size-input-group">
                  <input 
                    type="number"
                    v-model.number="cropperState.size"
                    @blur="validateCropperSize"
                    @keyup.enter="validateCropperSize"
                    class="size-input"
                    min="50"
                    max="500"
                    title="输入裁剪框边长（50-500）"
                  />
                  <span class="size-unit">px</span>
                </div>
                
                <button 
                  type="button"
                  class="size-btn"
                  @click="resizeCropper(20)"
                  title="放大裁剪框"
                >
                  放大
                  <i class="fas fa-plus"></i>
                </button>
              </div>
            </div>
          </div>
          
          <div class="modal-footer">
            <button type="button" class="btn btn-cancel" @click="closeAvatarUploadModal">取消</button>
            <button 
              v-if="avatarPreviewUrl"
              type="button" 
              class="btn btn-save" 
              @click="confirmAvatarCrop"
            >
              确认
            </button>
            <button 
              v-else
              type="button" 
              class="btn btn-save"
              disabled
            >
              请先选择图片
            </button>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted } from 'vue'
import axios from 'axios'

// ===== 接口客户端与工具 =====

const apiClient = axios.create({
  // 默认使用相对路径 /api，开发环境由 Vite 代理到 8000，生产环境由 Nginx 反向代理
  baseURL: import.meta.env?.VITE_API_BASE_URL || '/api',
  timeout: 10000
})
//api.interceptors.request.use
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token') || localStorage.getItem('token')
    if (token) {
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ===== 响应式状态 =====
// 活跃标签页 'intro'/'following'/'followers'/'anime'/'dynamics'
const activeTab = ref('intro')
// 动态筛选过滤器 'all'/'entry'/'review'
const dynamicFilter = ref('all')
// 正在编辑字段 'username'/'signature'/'introduction'
const editingField = ref('')
// 编辑/预览 'edit'/'preview'
const editMode = ref('edit')
// 编辑框与隐私框显示状态
const showEditModal = ref(false)
const showPrivacySettingsModal = ref(false)
// 头像上传模态框显示状态
const showAvatarUploadModal = ref(false)
// 是否为自己的个人空间
const isOwnProfile = ref(true)
// 关注状态（他人空间可见）
const isFollowing = ref(false)
// 资料加载状态
const profileLoading = ref(false)
const profileError = ref('')
// 头像上传相关状态
const avatarPreviewUrl = ref('')
const avatarCanvas = ref(null)
const avatarFileInput = ref(null)
const cropperState = reactive({
  x: 0,
  y: 0,
  size: 200,
  isDragging: false,
  dragStartX: 0,
  dragStartY: 0
})
// 编辑表单数据
const editFormData = reactive({
  username: '',
  signature: '',
  introduction: ''
})

// 用户基本信息
const userProfile = reactive({
  id: 1,
  username: '未登录',
  avatar: '',
  signature: '',
  followingCount: 0,
  followersCount: 0,
  animeCount: 0,
  introduction: ''
})
// 关注列表
const following = ref([])

function handFollowingListTabClick() {
  switchTab('following')
  getUserFollowingList()  // 不传参数或传空对象
}

async function getUserFollowingList(userId, params = {}) {
  userId=userProfile.id
  try {
    if (!userId) {
      throw new Error('用户ID不能为空')
    }

    const requestParams = {
      page: 1,
      limit: 20,
      ...params
    }

    console.log('请求关注列表参数:', { userId, ...requestParams })

    const response = await apiClient.get(`/personal_homepage_following_list/${userId}`, {
      params: requestParams
    })

    console.log('关注列表响应:', response.data)
    return response.data

  } catch (error) {
    console.error('获取用户关注列表失败:', error)
    if (error.response) {
      console.error('错误详情:', error.response.data)
    }
    throw error
  }
}
/*
const following = ref([
  { id: 101, username: '动漫迷小王', avatar: 'https://via.placeholder.com/50x50/ff69b4/ffffff?text=W', signature: '专业追番人' },
  { id: 102, username: '二次元少女', avatar: 'https://via.placeholder.com/50x50/ff1493/ffffff?text=G', signature: '萌豚一枚' }
])*/
// 粉丝列表
handfollowersListTabClick()
const followers = ref([])

function handfollowersListTabClick() {
  switchTab('followers')
  getUserfollowersList()  // 不传参数或传空对象
}

async function getUserfollowersList(userId, params = {}) {
  userId=userProfile.id
  try {
    if (!userId) {
      throw new Error('用户ID不能为空')
    }

    const requestParams = {
      page: 1,
      limit: 20,
      ...params
    }

    console.log('请求关注列表参数:', { userId, ...requestParams })

    const response = await apiClient.get(`/personal_homepage_follower_list/${userId}`, {
      params: requestParams
    })

    console.log('关注列表响应:', response.data)
    return response.data

  } catch (error) {
    console.error('获取用户关注列表失败:', error)
    if (error.response) {
      console.error('错误详情:', error.response.data)
    }
    throw error
  }
}
/*
const followers = ref([
  { id: 201, username: '番剧推荐官', avatar: 'https://via.placeholder.com/50x50/ff6347/ffffff?text=T', signature: '推荐好番' },
  { id: 202, username: '御宅族小李', avatar: 'https://via.placeholder.com/50x50/ffa500/ffffff?text=L', signature: '宅在家看番' }
])*/
// 追番列表
const animeList = ref([])

function handleanimeListTabClick() {
  switchTab('animeList')
  getUserAnimeList()  // 不传参数或传空对象
}

async function getUserAnimeList(userId, params = {}) {
  userId=userProfile.id
  try {
    if (!userId) {
      throw new Error('用户ID不能为空')
    }

    const requestParams = {
      page: 1,
      limit: 20,
      ...params
    }

    console.log('请求番剧列表参数:', { userId, ...requestParams })

    const response = await apiClient.get(`/personal_homepage_anime_list/${userId}`, {
      params: requestParams
    })

    console.log('番剧列表响应:', response.data)
    return response.data

  } catch (error) {
    console.error('获取用户番剧列表失败:', error)
    if (error.response) {
      console.error('错误详情:', error.response.data)
    }
    throw error
  }
}
/*
const animeList = ref([
  { id: 1001, title: '咒术回战', cover: 'https://via.placeholder.com/60x90/ff4500/ffffff?text=JJK', watchStatus: 'watching', watchStatusText: '在看', currentEpisode: 42, totalEpisodes: 50 },
  { id: 1002, title: '间谍过家家', cover: 'https://via.placeholder.com/60x90/32cd32/ffffff?text=SPY', watchStatus: 'watching', watchStatusText: '在看', currentEpisode: 25, totalEpisodes: 50 },
  { id: 1003, title: '鬼灭之刃', cover: 'https://via.placeholder.com/60x90/dc143c/ffffff?text=KNY', watchStatus: 'completed', watchStatusText: '已看', currentEpisode: 55, totalEpisodes: 55 }
])
  */
// 动态列表
const dynamics = ref([])

function handleDynamicTabClick() {
  switchTab('dynamics')
  getUserActivities()  // 不传参数或传空对象
}

async function getUserActivities(params = {}) {
  try {    
    const requestParams = {
      user_id: userProfile.id, // 添加 user_id
      page: 1,
      limit: 20,
      ...params
    }
    
    console.log('请求参数:', requestParams)
    
    const response = await apiClient.get('/user_activities/', {
      params: requestParams
    })
    
    console.log('完整响应:', response.data)
    
    if (response.data.code === 0) {
      const result = response.data.data
      dynamics = result.list
      pagination = result.pagination
      return result
    } else {
      throw new Error(response.data.message || '获取动态失败')
    }
  } catch (error) {
    console.error('获取用户动态失败:', error)
    if (error.response) {
      console.error('错误详情:', error.response.data)
    }
    throw error
  }
}
/*
const dynamics = ref([
  { id: 1, type: 'entry', username: '二次元爱好者', userAvatar: 'https://via.placeholder.com/40x40/ff6b9d/ffffff?text=U', animeTitle: '新的番剧条目', content: '', createdAt: '2025-01-15T10:30:00Z', likes: 5, comments: 2 },
  { id: 2, type: 'review', username: '二次元爱好者', userAvatar: 'https://via.placeholder.com/40x40/ff6b9d/ffffff?text=U', animeTitle: '间谍过家家', content: '超级温馨有趣的家庭喜剧！', createdAt: '2025-01-14T15:20:00Z', likes: 12, comments: 3 },
  { id: 3, type: 'review', username: '二次元爱好者', userAvatar: 'https://via.placeholder.com/40x40/ff6b9d/ffffff?text=U', animeTitle: '咒术回战', content: '剧情紧凑，战斗场面精彩！', createdAt: '2025-01-13T09:15:00Z', likes: 8, comments: 1 }
])
  */
// 隐私设置
const privacySettings = ref([
  { key: 'followers', label: '粉丝列表', description: '谁可以看到你的粉丝列表', value: 'public' },
  { key: 'following', label: '关注列表', description: '谁可以看到你的关注列表', value: 'public' },
  { key: 'anime_list', label: '追番列表', description: '谁可以看到你的追番列表', value: 'followers' },
  { key: 'dynamics', label: '动态', description: '谁可以看到你的动态', value: 'public' }
])

// 过滤动态列表 'all'/'entry'/'review'
const filteredDynamics = computed(() => {
  if (dynamicFilter.value === 'all') return dynamics.value
  return dynamics.value.filter(d => d.type === dynamicFilter.value)
})

// ===== 方法 =====

// ===== 接口：获取个人主页 / 他人主页 =====

// ===== 接口：获取当前登录用户的主页信息 =====GET /api/user/profile

// 组件挂载时默认拉取当前登录用户的主页信息

onMounted(() => {
  fetchCurrentUserProfile()
})

async function fetchCurrentUserProfile() {
  profileLoading.value = true
  profileError.value = ''
  try {
    const response = await apiClient.get('/user/profile')
    const result = response.data || {}
    console.log('response--------------------------')
    console.log(response)
    console.log('result----------------------------')
    console.log(result||'null')
    if (result.code !== 0 || !result.data) {
      throw new Error(result.message || '获取个人主页失败')
    }
    const data = result.data

    isOwnProfile.value = true
    applyProfilePayload(data)
  } catch (err) {
    console.error('获取个人主页失败:', err)
    profileError.value = err?.response?.data?.message || err?.message || '获取个人主页失败'
  } finally {
    profileLoading.value = false
  }
}

// 将后端返回的数据映射到前端 userProfile 等状态
function applyProfilePayload(data) {
  userProfile.id = data.id ?? userProfile.id
  userProfile.username = data.username || userProfile.username
  userProfile.avatar = data.avatar || userProfile.avatar
  userProfile.signature = data.signature || userProfile.signature
  // 文档中个人简介字段名为 bio，这里兼容 bio/introduction
  userProfile.introduction = data.bio || data.introduction || userProfile.introduction
  userProfile.followingCount = data.following_count ?? userProfile.followingCount
  userProfile.followersCount = data.follower_count ?? userProfile.followersCount
  // 如果后端补充了追番数量字段，也一并兼容
  if (typeof data.watch_count === 'number') {
    userProfile.animeCount = data.watch_count
  }

  // 如果后端返回隐私设置，可同步到 privacySettings
  if (data.privacy && typeof data.privacy === 'object') {
    privacySettings.value = privacySettings.value.map(setting => {
      let newValue = setting.value
      if (setting.key === 'followers' && data.privacy.followers) {
        newValue = data.privacy.followers
      } else if (setting.key === 'following' && data.privacy.follows) {
        newValue = data.privacy.follows
      } else if (setting.key === 'anime_list' && data.privacy.watchlist) {
        newValue = data.privacy.watchlist
      } else if (setting.key === 'dynamics' && data.privacy.activities) {
        newValue = data.privacy.activities
      }
      return { ...setting, value: newValue }
    })
  }
}





// 实现头像上传功能
function handleEditAvatar() {
  showAvatarUploadModal.value = true
}
function handleFileSelect(event) {
  const file = event.target.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    alert('请选择图片文件')
    return
  }
  const reader = new FileReader()
  reader.onload = (e) => {
    avatarPreviewUrl.value = e.target?.result || ''
    cropperState.x = 0
    cropperState.y = 0
    cropperState.size = 200
    nextTick(() => drawCropper())
  }
  reader.readAsDataURL(file)
}
function drawCropper() {
  const canvas = avatarCanvas.value
  if (!canvas || !avatarPreviewUrl.value) return
  
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  const img = new Image()
  img.onload = () => {
    // 清空 Canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
    // 绘制原图（缩放显示）
    const scale = Math.min(canvas.width / img.width, canvas.height / img.height)
    const displayWidth = img.width * scale
    const displayHeight = img.height * scale
    const offsetX = (canvas.width - displayWidth) / 2
    const offsetY = (canvas.height - displayHeight) / 2
    
    ctx.drawImage(img, offsetX, offsetY, displayWidth, displayHeight)
    
    // 先绘制半透明黑色遮罩覆盖整个 Canvas
    ctx.fillStyle = 'rgba(0, 0, 0, 0.6)'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    
    // 再清空裁剪区域以显示原图
    ctx.clearRect(cropperState.x, cropperState.y, cropperState.size, cropperState.size)
    
    // 在清空区域上重新绘制原图（这样显示的是原图而不是透明）
    // 需要将 Canvas 坐标转换到原图坐标
    const cropStartXInOriginal = (cropperState.x - offsetX) / scale
    const cropStartYInOriginal = (cropperState.y - offsetY) / scale
    const cropSizeInOriginal = cropperState.size / scale
    
    ctx.drawImage(
      img,
      cropStartXInOriginal,
      cropStartYInOriginal,
      cropSizeInOriginal,
      cropSizeInOriginal,
      cropperState.x,
      cropperState.y,
      cropperState.size,
      cropperState.size
    )
    
    // 绘制裁剪框边框（简洁设计）
    ctx.strokeStyle = '#ff6b9d'
    ctx.lineWidth = 2
    ctx.strokeRect(cropperState.x, cropperState.y, cropperState.size, cropperState.size)
  }
  img.src = avatarPreviewUrl.value
}
// 处理裁剪框拖动
// 处理鼠标按下（仅支持移动裁剪框，不支持调整大小）
function handleCanvasMouseDown(event) {
  const canvas = avatarCanvas.value
  if (!canvas) return
  
  const rect = canvas.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  // 检查是否点击在裁剪框内
  if (x >= cropperState.x && x <= cropperState.x + cropperState.size &&
      y >= cropperState.y && y <= cropperState.y + cropperState.size) {
    // 进入拖动模式
    cropperState.isDragging = true
    cropperState.dragStartX = x - cropperState.x
    cropperState.dragStartY = y - cropperState.y
  }
}

// 处理鼠标移动（移动裁剪框）
function handleCanvasMouseMove(event) {
  if (!cropperState.isDragging || !avatarCanvas.value) return
  
  const canvas = avatarCanvas.value
  const rect = canvas.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  // 计算新位置
  let newX = x - cropperState.dragStartX
  let newY = y - cropperState.dragStartY
  
  // 限制边界，不超出 Canvas
  newX = Math.max(0, Math.min(newX, canvas.width - cropperState.size))
  newY = Math.max(0, Math.min(newY, canvas.height - cropperState.size))
  
  cropperState.x = newX
  cropperState.y = newY
  
  drawCropper()
}

// 处理鼠标抬起（停止拖动）
function handleCanvasMouseUp() {
  cropperState.isDragging = false
}

function resizeCropper(delta) {
  cropperState.size = Math.max(50, Math.min(500, cropperState.size + delta))
  const canvas = avatarCanvas.value
  if (canvas) {
    if (cropperState.x + cropperState.size > canvas.width)
      cropperState.x = Math.max(0, canvas.width - cropperState.size)
    if (cropperState.y + cropperState.size > canvas.height)
      cropperState.y = Math.max(0, canvas.height - cropperState.size)
  }
  drawCropper()
}

function validateCropperSize() {
  cropperState.size = Math.max(50, Math.min(500, cropperState.size))
  const canvas = avatarCanvas.value
  if (canvas) {
    if (cropperState.x + cropperState.size > canvas.width)
      cropperState.x = Math.max(0, canvas.width - cropperState.size)
    if (cropperState.y + cropperState.size > canvas.height)
      cropperState.y = Math.max(0, canvas.height - cropperState.size)
  }
  drawCropper()
}
// 确认头像并裁剪
function confirmAvatarCrop() {
  if (!avatarCanvas.value || !avatarPreviewUrl.value) {
    alert('请先选择图片')
    return
  }
  
  const canvas = avatarCanvas.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  // 创建临时 Canvas 用于裁剪
  const cropCanvas = document.createElement('canvas')
  cropCanvas.width = 200
  cropCanvas.height = 200
  const cropCtx = cropCanvas.getContext('2d')
  if (!cropCtx) return
  
  // 从原图中截取裁剪区域
  const img = new Image()
  img.onload = () => {
    // 重新计算裁剪坐标（因为显示时有缩放）
    const scale = Math.min(canvas.width / img.width, canvas.height / img.height)
    const displayWidth = img.width * scale
    const displayHeight = img.height * scale
    const offsetX = (canvas.width - displayWidth) / 2
    const offsetY = (canvas.height - displayHeight) / 2
    
    // 计算在原图中的实际裁剪坐标
    const cropX = (cropperState.x - offsetX) / scale
    const cropY = (cropperState.y - offsetY) / scale
    const cropSize = cropperState.size / scale
    
    cropCtx.drawImage(
      img,
      Math.max(0, cropX),
      Math.max(0, cropY),
      cropSize,
      cropSize,
      0,
      0,
      200,
      200
    )
    
    // 将裁剪后的图片保存为 Data URL
    const croppedImageUrl = cropCanvas.toDataURL('image/jpeg', 0.9)
    
    // 更新用户头像
    userProfile.avatar = croppedImageUrl
    //上传新的头像
    uploadCroppedAvatar(croppedImageUrl)
    // 关闭模态框
    closeAvatarUploadModal()
  }
  img.src = avatarPreviewUrl.value
}

async function uploadCroppedAvatar(croppedImageUrl) {
  try {
    const avatarFile = dataURLtoFile(croppedImageUrl, 'avatar.jpg')
    
    const formData = new FormData()
    formData.append('avatar', avatarFile)

    // 直接使用现有的 apiClient
    const response = await apiClient.post('/user/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        // Authorization 头已经在拦截器中自动添加了
      }
    })

    console.log('头像上传成功:', response.data)
    return response.data
    
  } catch (error) {
    console.error('头像上传失败:', error)
    throw error
  }
}

function dataURLtoFile(dataURL, filename) {
  // 将 dataURL 拆解
  const arr = dataURL.split(',')
  const mime = arr[0].match(/:(.*?);/)[1]
  const bstr = atob(arr[1])
  let n = bstr.length
  const u8arr = new Uint8Array(n)
  
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n)
  }
  
  // 创建 File 对象
  return new File([u8arr], filename, { type: mime })
}

function closeAvatarUploadModal() {
  showAvatarUploadModal.value = false
  avatarPreviewUrl.value = ''
  cropperState.x = 0
  cropperState.y = 0
  cropperState.size = 200
  cropperState.isDragging = false
}

function startEditField(field) {
  editingField.value = field
  editMode.value = 'edit'
  
  if (field === 'username') editFormData.username = userProfile.username
  else if (field === 'signature') editFormData.signature = userProfile.signature
  else if (field === 'introduction') editFormData.introduction = userProfile.introduction

  showEditModal.value = true
}

function closeEditModal() {
  showEditModal.value = false
  editingField.value = ''
  editMode.value = 'edit'
}

function getEditModalTitle() {
  const titles = {
    username: '编辑用户名',
    signature: '编辑个性签名',
    introduction: '编辑个人介绍'
  }
  return titles[editingField.value] || '编辑'
}

function saveEdit() {
  if (editingField.value === 'username') {
    if (!editFormData.username.trim()) {
      alert('用户名不能为空')
      return
    }
    userProfile.username = editFormData.username
  } else if (editingField.value === 'signature') {
    userProfile.signature = editFormData.signature
  } else if (editingField.value === 'introduction') {
    userProfile.introduction = editFormData.introduction
  }

  closeEditModal()
}

function switchTab(tab) {
  activeTab.value = tab
}

function renderMarkdown(text) {
  if (!text) return ''
  let html = text
    .replace(/^### (.*?)$/gm, '<h3>$1</h3>')
    .replace(/^## (.*?)$/gm, '<h2>$1</h2>')
    .replace(/^# (.*?)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\_(.*?)\_/g, '<em>$1</em>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^- (.*?)$/gm, '<li>$1</li>')
  
  if (html.includes('<li>')) {
    html = html.replace(/(<li>.*?<\/li>)/s, '<ul>$1</ul>')
  }
  
  if (!html.startsWith('<p>')) html = '<p>' + html
  if (!html.endsWith('</p>')) html = html + '</p>'
  
  return html
}

function formatTime(isoString) {
  const date = new Date(isoString)
  const now = new Date()
  const diff = now - date
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) return `${days}天前`
  if (hours > 0) return `${hours}小时前`
  if (minutes > 0) return `${minutes}分钟前`
  return '刚刚'
}

//计算了关注/取关引起的粉丝数变化
function toggleFollowStatus() {
  isFollowing.value = !isFollowing.value
  if (isFollowing.value) {
    userProfile.followersCount++
  } else {
    userProfile.followersCount = Math.max(0, userProfile.followersCount - 1)
  }
}
//检查某用户是否在关注列表中
function isFollowingUser(userId) {
  return following.value.some(u => u.id === userId)
}

function savePrivacySettings() {
  alert('隐私设置已保存')
  showPrivacySettingsModal.value = false
}

</script>

<style scoped>
* {
  box-sizing: border-box;
}

.personal-space-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
}

/* ===== 基本信息栏 ===== */
.user-info-card {
  background: white;
  border-radius: 12px;
  padding: 40px;
  margin-bottom: 30px;
  display: flex;
  gap: 40px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  align-items: flex-start;
}

.avatar-section {
  flex-shrink: 0;
}

.avatar-container {
  position: relative;
  width: 140px;
  height: 140px;
  border-radius: 50%;
  overflow: hidden;
  border: 3px solid #ff6b9d;
  box-shadow: 0 4px 15px rgba(255, 107, 157, 0.3);
}

.avatar-container.editable {
  cursor: pointer;
}

.avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.3s;
  gap: 5px;
}

.avatar-container.editable:hover .avatar-overlay {
  opacity: 1;
}

.avatar-overlay i {
  font-size: 24px;
}

.info-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.user-header {
  display: flex;
  align-items: center;
  gap: 15px;
}

.username {
  font-size: 32px;
  font-weight: bold;
  color: #2c3e50;
  margin: 0;
}

.edit-btn {
  background: rgba(255, 107, 157, 0.1);
  border: 1px solid #ffc2d9;
  color: #ff6b9d;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  padding: 0;
}

.edit-btn:hover {
  background: rgba(255, 107, 157, 0.2);
  transform: scale(1.05);
}

.signature-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.signature {
  font-size: 15px;
  color: #7f8c8d;
  margin: 0;
  flex: 1;
}

.stats-bar {
  display: flex;
  gap: 50px;
  padding: 20px 0;
  border-top: 1px solid #ecf0f1;
  border-bottom: 1px solid #ecf0f1;
}

.stat-item {
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  padding: 5px 10px;
  border-radius: 8px;
}

.stat-item:hover {
  background: rgba(255, 107, 157, 0.05);
}

.stat-number {
  display: block;
  font-size: 22px;
  font-weight: bold;
  color: #ff6b9d;
}

.stat-label {
  display: block;
  font-size: 13px;
  color: #95a5a6;
  margin-top: 5px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.follow-btn,
.message-btn,
.settings-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.follow-btn {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
}

.follow-btn.is-following {
  background: white;
  color: #ff6b9d;
  border: 2px solid #ff6b9d;
}

.settings-btn {
  background: white;
  color: #7f8c8d;
  border: 2px solid #ecf0f1;
}

/* ===== 筛选展示栏 ===== */
.content-area {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.content-tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid #ecf0f1;
  padding: 0;
  margin: 0;
  overflow-x: auto;
}

.tab-btn {
  flex: 0 0 auto;
  padding: 16px 24px;
  border: none;
  background: white;
  color: #7f8c8d;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all 0.3s;
  white-space: nowrap;
}

.tab-btn:hover {
  color: #2c3e50;
  background: #f8f9fa;
}

.tab-btn.active {
  color: #ff6b9d;
  border-bottom-color: #ff6b9d;
  background: #fff9fc;
}

.tab-content {
  min-height: 400px;
  position: relative;
}

.tab-pane {
  padding: 40px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #95a5a6;
}

.empty-state i {
  font-size: 48px;
  color: #ecf0f1;
  margin-bottom: 20px;
  display: block;
}

.empty-state p {
  font-size: 16px;
  margin: 0;
}

/* 介绍 */
.intro-container {
  max-width: 800px;
}

.intro-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
}

.intro-header h3 {
  font-size: 20px;
  color: #2c3e50;
  margin: 0;
}

.edit-btn-large {
  padding: 8px 16px;
  background: rgba(255, 107, 157, 0.1);
  border: 1px solid #ffc2d9;
  color: #ff6b9d;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.edit-btn-large:hover {
  background: rgba(255, 107, 157, 0.2);
}

.intro-display {
  font-size: 15px;
  line-height: 1.8;
  color: #34495e;
}

.markdown-content {
  white-space: pre-wrap;
  word-break: break-word;
}

.markdown-content h1 {
  font-size: 24px;
  border-bottom: 2px solid #ff6b9d;
  padding-bottom: 8px;
  margin: 20px 0 10px 0;
}

.markdown-content h2 {
  font-size: 20px;
  color: #ff6b9d;
  margin: 20px 0 10px 0;
}

.markdown-content h3 {
  font-size: 16px;
  margin: 15px 0 8px 0;
}

.markdown-content ul {
  list-style: disc inside;
  margin: 10px 0;
  padding-left: 20px;
}

.markdown-content li {
  margin: 5px 0;
}

.markdown-content p {
  margin: 10px 0;
}

/* 列表 */
.list-container {
  max-width: 600px;
}

.list-container h3 {
  font-size: 18px;
  color: #2c3e50;
  margin: 0 0 20px 0;
}

.user-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  transition: all 0.3s;
}

.user-item:hover {
  background: #ecf0f1;
}

.user-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #ecf0f1;
}

.user-info {
  flex: 1;
}

.user-name {
  font-weight: 500;
  color: #2c3e50;
  margin-bottom: 4px;
}

.user-signature {
  font-size: 12px;
  color: #95a5a6;
}

.action-icon-btn,
.follow-back-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
}

.action-icon-btn {
  background: #ecf0f1;
  color: #7f8c8d;
}

.action-icon-btn:hover {
  background: #e74c3c;
  color: white;
}

.follow-back-btn {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
}

.follow-back-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 107, 157, 0.3);
}

/* 追番列表 */
.anime-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.anime-item {
  display: flex;
  gap: 15px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  transition: all 0.3s;
}

.anime-item:hover {
  background: #ecf0f1;
  transform: translateX(4px);
}

.anime-cover {
  flex-shrink: 0;
  width: 60px;
  height: 90px;
  border-radius: 4px;
  overflow: hidden;
  background: #ecf0f1;
}

.anime-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.anime-info {
  flex: 1;
}

.anime-title {
  font-weight: 500;
  color: #2c3e50;
  margin-bottom: 8px;
}

.anime-meta {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 12px;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 3px;
  font-weight: 500;
  font-size: 11px;
}

.status-watching {
  background: #fff3cd;
  color: #856404;
}

.status-completed {
  background: #d4edda;
  color: #155724;
}

.episode-info {
  color: #7f8c8d;
}

/* 时间轴 */
.timeline-container {
  max-width: 700px;
}

.timeline-container h3 {
  font-size: 18px;
  color: #2c3e50;
  margin: 0 0 20px 0;
}

.dynamic-filters {
  display: flex;
  gap: 10px;
  margin-bottom: 25px;
}

.filter-btn {
  padding: 8px 16px;
  border: 2px solid #ecf0f1;
  background: white;
  color: #7f8c8d;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
}

.filter-btn:hover {
  border-color: #ff6b9d;
  color: #ff6b9d;
}

.filter-btn.active {
  background: #ff6b9d;
  border-color: #ff6b9d;
  color: white;
}

.timeline {
  position: relative;
  padding-left: 30px;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(to bottom, #ff6b9d, #c3cfe2);
}

.timeline-item {
  position: relative;
  margin-bottom: 25px;
  padding-left: 20px;
}

.timeline-marker {
  position: absolute;
  left: -35px;
  top: 5px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: white;
  border: 3px solid #ff6b9d;
  transition: all 0.3s;
}

.timeline-item:hover .timeline-marker {
  width: 20px;
  height: 20px;
  left: -37px;
  top: 3px;
  box-shadow: 0 0 0 4px rgba(255, 107, 157, 0.2);
}

.timeline-marker.entry {
  border-color: #3498db;
}

.timeline-marker.review {
  border-color: #e74c3c;
}

.timeline-content {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  transition: all 0.3s;
}

.timeline-item:hover .timeline-content {
  background: #ecf0f1;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.dynamic-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.user-brief {
  display: flex;
  align-items: center;
  gap: 8px;
}

.avatar-small {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
}

.username-text {
  font-weight: 500;
  color: #2c3e50;
  font-size: 13px;
}

.timestamp {
  font-size: 12px;
  color: #95a5a6;
}

.dynamic-body {
  margin-bottom: 10px;
}

.dynamic-body p {
  margin: 0;
  font-size: 14px;
  color: #34495e;
}

.dynamic-body strong {
  color: #ff6b9d;
}

.dynamic-actions {
  display: flex;
  gap: 12px;
}

.action-btn {
  padding: 4px 10px;
  border: 1px solid #ecf0f1;
  background: white;
  color: #95a5a6;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.3s;
}

.action-btn:hover {
  border-color: #ff6b9d;
  color: #ff6b9d;
}

/* ===== 模态框 ===== */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #ecf0f1;
}

.modal-header h3 {
  font-size: 18px;
  color: #2c3e50;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  color: #95a5a6;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: #f8f9fa;
  color: #2c3e50;
}

.modal-body {
  padding: 20px;
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-input,
.form-textarea {
  padding: 10px 12px;
  border: 1px solid #ecf0f1;
  border-radius: 6px;
  font-family: inherit;
  font-size: 14px;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #ff6b9d;
  box-shadow: 0 0 0 3px rgba(255, 107, 157, 0.1);
}

.char-counter {
  text-align: right;
  font-size: 12px;
  color: #95a5a6;
}

.markdown-editor {
  gap: 0;
}

.editor-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid #ecf0f1;
  margin-bottom: 15px;
}

.editor-tab {
  flex: 1;
  padding: 10px;
  border: none;
  background: white;
  color: #7f8c8d;
  font-size: 13px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.3s;
}

.editor-tab.active {
  color: #ff6b9d;
  border-bottom-color: #ff6b9d;
}

.markdown-hint {
  margin-top: 10px;
  font-size: 12px;
  color: #95a5a6;
}

.markdown-hint a {
  color: #ff6b9d;
  text-decoration: none;
}

.markdown-preview {
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 14px;
  line-height: 1.8;
  color: #34495e;
  max-height: 400px;
  overflow-y: auto;
}

.privacy-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 15px 0;
  border-bottom: 1px solid #ecf0f1;
}

.privacy-item:last-child {
  border-bottom: none;
}

.privacy-label h4 {
  font-size: 14px;
  color: #2c3e50;
  margin: 0 0 4px 0;
}

.privacy-label p {
  font-size: 12px;
  color: #95a5a6;
  margin: 0;
}

.privacy-select {
  padding: 6px 10px;
  border: 1px solid #ecf0f1;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 20px;
  border-top: 1px solid #ecf0f1;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s;
}

.btn-cancel {
  background: #ecf0f1;
  color: #7f8c8d;
}

.btn-cancel:hover {
  background: #bdc3c7;
}

.btn-save {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
}

.btn-save:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 107, 157, 0.3);
}

/* ===== 头像上传 ===== */
.avatar-upload-modal {
  max-width: 600px;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: #95a5a6;
}

.upload-placeholder i {
  font-size: 48px;
  margin-bottom: 15px;
  color: #ecf0f1;
}

.upload-placeholder p {
  font-size: 16px;
  margin: 0 0 20px 0;
  color: #7f8c8d;
}

.btn-upload {
  padding: 12px 24px;
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-upload:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 107, 157, 0.3);
}

.crop-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.crop-header {
  text-align: center;
}

.crop-header h4 {
  font-size: 16px;
  color: #2c3e50;
  margin: 0 0 5px 0;
}

.crop-header p {
  font-size: 12px;
  color: #95a5a6;
  margin: 0;
}

.crop-canvas {
  display: block;
  width: 100%;
  max-width: 500px;
  height: auto;
  border: 2px solid #ecf0f1;
  border-radius: 8px;
  cursor: move;
  background: #f8f9fa;
  margin: 0 auto;
}

.crop-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 15px 0;
}

.size-btn {
  padding: 8px 14px;
  border: 1px solid #ecf0f1;
  background: white;
  color: #7f8c8d;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.3s;
  white-space: nowrap;
}

.size-btn:hover {
  border-color: #ff6b9d;
  color: #ff6b9d;
  background: #fff9fc;
}

.size-input-group {
  display: flex;
  align-items: center;
  gap: 4px;
  background: white;
  border: 1px solid #ecf0f1;
  border-radius: 6px;
  padding: 0 8px;
}

.size-input {
  width: 60px;
  padding: 8px 0;
  border: none;
  text-align: center;
  font-size: 13px;
  font-weight: 500;
  color: #2c3e50;
  background: transparent;
  outline: none;
}

.size-input:focus {
  background: transparent;
}

.size-input::-webkit-outer-spin-button,
.size-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.size-input[type=number] {
  -moz-appearance: textfield;
  appearance: textfield;
}

.size-unit {
  font-size: 12px;
  color: #95a5a6;
  font-weight: 500;
}

/* ===== 响应式设计 ===== */
@media (max-width: 768px) {
  .user-info-card {
    flex-direction: column;
    padding: 20px;
    gap: 20px;
    text-align: center;
  }

  .avatar-container {
    width: 100px;
    height: 100px;
    margin: 0 auto;
  }

  .user-header {
    justify-content: center;
  }

  .signature-row {
    justify-content: center;
  }

  .stats-bar {
    justify-content: space-around;
  }

  .action-buttons {
    justify-content: center;
  }

  .tab-pane {
    padding: 20px;
  }

  .modal {
    width: 95%;
  }
}
</style>
