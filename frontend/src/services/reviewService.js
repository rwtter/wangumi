// src/services/reviewService.js
import axios from 'axios';

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: import.meta.env?.VITE_API_BASE_URL || '',
  timeout: 10000,
});

// 请求拦截器 - 自动添加 token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * 创建或更新番剧评价
 * @param {number} animeId - 番剧ID
 * @param {number} score - 评分 (1-10)
 * @param {string} comment - 评论内容 (可选)
 * @returns {Promise}
 */
export const createAnimeReview = async (animeId, score, comment = '') => {
  try {
    const response = await apiClient.post('/api/reviews/anime', {
      animeId: animeId,
      score: score,
      comment: comment
    });
    return response.data;
  } catch (error) {
    console.error('创建评价失败:', error);
    throw error;
  }
};

/**
 * 获取用户对某番剧的评价
 * @param {number} animeId - 番剧ID
 * @returns {Promise}
 */
export const getUserAnimeReview = async (animeId) => {
  try {
    const response = await apiClient.get('/api/reviews/anime/get', {
      params: { anime_id: animeId }
    });
    return response.data;
  } catch (error) {
    console.error('获取评价失败:', error);
    throw error;
  }
};

/**
 * 更新评价
 * @param {number} reviewId - 评价ID
 * @param {number} score - 评分 (1-10)
 * @param {string} comment - 评论内容
 * @returns {Promise}
 */
export const updateReview = async (reviewId, score, comment) => {
  try {
    const response = await apiClient.patch(`/api/reviews/${reviewId}`, {
      score: score,
      comment: comment
    });
    return response.data;
  } catch (error) {
    console.error('更新评价失败:', error);
    throw error;
  }
};

/**
 * 创建回复
 * @param {number} commentId - 评论ID
 * @param {string} content - 回复内容
 * @returns {Promise}
 */
export const createReply = async (commentId, content) => {
  try {
    const response = await apiClient.post(`/api/comments/${commentId}/replies/`, {
      content: content
    });
    return response.data;
  } catch (error) {
    console.error('创建回复失败:', error);
    throw error;
  }
};

/**
 * 获取评价的回复列表（暂时模拟，等后端接口）
 * @param {number} reviewId - 评价ID
 * @returns {Promise}
 */
export const getReplies = async (reviewId) => {
  try {
    // 当后端接口准备好后，取消注释下面的代码
    /*
    const response = await apiClient.get(`/api/replies/${reviewId}`);
    return response.data;
    */

    // 临时模拟返回空数组
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          code: 200,
          message: 'success',
          data: {
            reviewId: reviewId,
            replies: [],
            total: 0
          }
        });
      }, 300);
    });
  } catch (error) {
    console.error('获取回复失败:', error);
    throw error;
  }
};

/**
 * 点赞评价
 * @param {number} commentId - 评论ID
 * @returns {Promise}
 */
export const likeReview = async (commentId) => {
  try {
    const response = await apiClient.post(`/api/comments/${commentId}/like/`);
    return response.data;
  } catch (error) {
    console.error('点赞失败:', error);
    throw error;
  }
};

/**
 * 取消点赞评价
 * @param {number} commentId - 评论ID
 * @returns {Promise}
 */
export const unlikeReview = async (commentId) => {
  try {
    const response = await apiClient.delete(`/api/comments/${commentId}/like/`);
    return response.data;
  } catch (error) {
    console.error('取消点赞失败:', error);
    throw error;
  }
};

/**
 * 举报评价
 * @param {number} commentId - 评论ID
 * @param {string} category - 举报分类 (SPAM, HARASSMENT, INAPPROPRIATE, SPOILER, OTHER)
 * @param {string} reason - 补充说明 (可选, 最多500字符)
 * @returns {Promise}
 */
export const reportReview = async (commentId, category, reason = '') => {
  try {
    const response = await apiClient.post(`/api/comments/${commentId}/reports/`, {
      category: category,
      reason: reason
    });
    return response.data;
  } catch (error) {
    console.error('举报失败:', error);
    throw error;
  }
};
