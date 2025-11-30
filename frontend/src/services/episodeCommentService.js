// src/services/episodeCommentService.js
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
 * 创建单集评论
 * @param {number} episodeId - 单集ID
 * @param {number} score - 评分 (1-10)
 * @param {string} content - 评论内容 (1-500字符)
 * @returns {Promise}
 */
export const createEpisodeComment = async (episodeId, score, content) => {
  try {
    const response = await apiClient.post('/api/comments/', {
      scope: 'EPISODE',
      object_id: episodeId,
      score: score,
      content: content
    });
    return response.data;
  } catch (error) {
    console.error('创建单集评论失败:', error);
    throw error;
  }
};

/**
 * 获取单集评论列表
 * @param {number} episodeId - 单集ID
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码,默认1
 * @param {number} params.page_size - 每页数量,默认20,最大50
 * @param {string} params.order_by - 排序方式: time_desc / time_asc / likes_desc
 * @param {number} params.min_score - 最低评分(用于过滤)
 * @param {number} params.max_score - 最高评分(用于过滤)
 * @returns {Promise}
 */
export const getEpisodeComments = async (episodeId, params = {}) => {
  try {
    const response = await apiClient.get('/api/comments/', {
      params: {
        scope: 'EPISODE',
        object_id: episodeId,
        page: params.page || 1,
        page_size: params.page_size || 20,
        order_by: params.order_by || 'time_desc',
        min_score: params.min_score,
        max_score: params.max_score
      }
    });
    return response.data;
  } catch (error) {
    console.error('获取单集评论列表失败:', error);
    throw error;
  }
};

/**
 * 回复评论
 * @param {number} commentId - 评论ID
 * @param {string} content - 回复内容 (1-500字符)
 * @returns {Promise}
 */
export const replyToComment = async (commentId, content) => {
  try {
    // 验证参数
    if (!commentId) {
      throw new Error('commentId 不能为空');
    }
    if (!content || content.trim().length === 0) {
      throw new Error('回复内容不能为空');
    }
    if (content.length > 500) {
      throw new Error('回复内容不能超过500字符');
    }

    console.log('发送回复请求:', {
      url: `/api/comments/${commentId}/replies/`,
      commentId,
      content: content.trim()
    });

    const response = await apiClient.post(`/api/comments/${commentId}/replies/`, {
      content: content.trim()
    });

    console.log('回复请求成功:', response.data);
    return response.data;
  } catch (error) {
    console.error('回复评论失败:', {
      commentId,
      error: error.response?.data || error.message,
      status: error.response?.status
    });
    throw error;
  }
};

/**
 * 获取评论的回复列表
 * @param {number} commentId - 评论ID
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码,默认1
 * @param {number} params.page_size - 每页数量,默认20,最大50
 * @param {string} params.order_by - 排序方式: time_desc / time_asc / likes_desc
 * @returns {Promise}
 */
export const getCommentReplies = async (commentId, params = {}) => {
  try {
    const response = await apiClient.get(`/api/comments/${commentId}/replies/`, {
      params: {
        page: params.page || 1,
        page_size: params.page_size || 20,
        order_by: params.order_by || 'time_desc'
      }
    });
    return response.data;
  } catch (error) {
    console.error('获取回复列表失败:', error);
    throw error;
  }
};

/**
 * 点赞/取消点赞评论
 * @param {number} commentId - 评论ID
 * @returns {Promise}
 */
export const likeComment = async (commentId) => {
  try {
    const response = await apiClient.post(`/api/comments/${commentId}/like/`);
    return response.data;
  } catch (error) {
    console.error('点赞评论失败:', error);
    throw error;
  }
};

/**
 * 取消点赞评论
 * @param {number} commentId - 评论ID
 * @returns {Promise}
 */
export const unlikeComment = async (commentId) => {
  try {
    const response = await apiClient.delete(`/api/comments/${commentId}/like/`);
    return response.data;
  } catch (error) {
    console.error('取消点赞失败:', error);
    throw error;
  }
};

/**
 * 举报评论
 * @param {number} commentId - 评论ID
 * @param {string} category - 举报类型 (SPAM, OFFENSIVE, ILLEGAL, OTHER)
 * @param {string} reason - 理由补充说明 (可选)
 * @returns {Promise}
 */
export const reportComment = async (commentId, category, reason = '') => {
  try {
    const response = await apiClient.post(`/api/comments/${commentId}/reports/`, {
      category: category,
      reason: reason
    });
    return response.data;
  } catch (error) {
    console.error('举报评论失败:', error);
    throw error;
  }
};
