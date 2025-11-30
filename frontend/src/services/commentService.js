// src/services/commentService.js
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
 * 创建评论（适用于条目、番剧、单集等）
 * @param {string} scope - 评论范围 (ANIME, EPISODE, ITEM)
 * @param {number} objectId - 对应的ID（番剧ID/单集ID/条目ID）
 * @param {number} score - 评分 (1-10)
 * @param {string} content - 评论内容
 * @returns {Promise}
 */
export const createComment = async (scope, objectId, score, content = '') => {
  try {
    const requestData = {
      scope: scope,
      object_id: objectId,
      score: score,
      content: content.trim()
    };

    console.log('创建评论请求:', requestData);

    const response = await apiClient.post('/api/comments/', requestData);
    console.log('创建评论响应:', response.data);
    return response.data;
  } catch (error) {
    console.error('创建评论失败:', error);
    console.error('错误详情:', error.response?.data);
    throw error;
  }
};

/**
 * 获取评论列表
 * @param {string} scope - 评论范围 (ANIME, EPISODE, ITEM)
 * @param {number} objectId - 对应的ID（番剧ID/单集ID/条目ID）
 * @param {object} params - 其他参数
 * @returns {Promise}
 */
export const getComments = async (scope, objectId, params = {}) => {
  try {
    const queryParams = {
      scope,
      object_id: objectId,
      page: params.page || 1,
      page_size: params.pageSize || 20,
      order_by: params.orderBy || 'time_desc',
      ...params
    };

    console.log('发送评论请求参数:', queryParams);
    console.log('请求URL: /api/comments/');

    // 使用GET请求发送query参数
    const response = await apiClient.get('/api/comments/', { params: queryParams });
    console.log('评论API响应:', response.data);
    return response.data;
  } catch (error) {
    console.error('获取评论列表失败:', error);
    console.error('错误详情:', error.response?.data);
    throw error;
  }
};

/**
 * 点赞评论
 * @param {number} commentId - 评论ID
 * @returns {Promise}
 */
export const likeComment = async (commentId) => {
  try {
    const response = await apiClient.post(`/api/comments/${commentId}/like/`);
    return response.data;
  } catch (error) {
    console.error('点赞失败:', error);
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
 * 获取回复列表
 * @param {number} commentId - 评论ID
 * @param {object} params - 查询参数
 * @returns {Promise}
 */
export const getReplies = async (commentId, params = {}) => {
  try {
    const queryParams = {
      page: params.page || 1,
      page_size: params.pageSize || 20,
      order_by: params.orderBy || 'time_desc'
    };

    console.log('获取回复请求参数:', { commentId, queryParams });

    const response = await apiClient.get(`/api/comments/${commentId}/replies/`, { params: queryParams });
    console.log('获取回复响应:', response.data);
    return response.data;
  } catch (error) {
    console.error('获取回复失败:', error);
    console.error('错误详情:', error.response?.data);
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
    const requestData = {
      content: content
    };

    console.log('创建回复请求:', { commentId, requestData, url: `/api/comments/${commentId}/replies/` });

    const response = await apiClient.post(`/api/comments/${commentId}/replies/`, requestData);
    console.log('创建回复响应:', response.data);
    return response.data;
  } catch (error) {
    console.error('创建回复失败:', error);
    console.error('错误详情:', error.response?.data);
    throw error;
  }
};

/**
 * 举报评论
 * @param {number} commentId - 评论ID
 * @param {string} category - 举报分类
 * @param {string} reason - 举报原因
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
    console.error('举报失败:', error);
    throw error;
  }
};
