// src/services/animeService.js
import axios from 'axios';

// 创建 axios 实例，baseURL 从环境变量读取
const apiClient = axios.create({
  baseURL: import.meta.env?.VITE_API_BASE_URL || '',
  timeout: 10000,
});

// 统一响应结构规范化函数
function normalizeAnimeListResponse(raw) {
  const data = raw?.data ?? raw ?? {};

  // 兼容多种后端返回字段
  const list =
    data.list ||
    data.items ||
    data.results ||
    data.data?.list ||
    data.data?.items ||
    [];

  const page =
    data.page ?? data.currentPage ?? data.pageNum ?? data.data?.page ?? 1;
  const limit =
    data.limit ?? data.pageSize ?? data.size ?? data.data?.limit ?? 12;
  const total =
    data.total ?? data.totalCount ?? data.totalElements ?? data.data?.total ?? list.length;
  const pages =
    data.pages ?? data.totalPages ?? Math.ceil((Number(total) || 0) / (Number(limit) || 1));

  return {
    code: 0,
    message: 'success',
    data: {
      list,
      pagination: {
        page: Number(page) || 1,
        limit: Number(limit) || 12,
        total: Number(total) || 0,
        pages: Number(pages) || 0,
      },
    },
  };
}

// 获取动漫列表 API
export const getAnimeList = async (params = {}) => {
  try {
    const query = {
      sort: params.sort,
      // 分类可能是数组或字符串：后端若需要以逗号分隔，进行转换
      category: Array.isArray(params.category)
        ? params.category.join(',')
        : params.category,
      page: params.page,
      limit: params.limit,
    };

    const response = await apiClient.get('/api/anime', { params: query });

    // 如果后端已经使用 { code, message, data }，优先使用；否则做规范化
    const respData = response?.data;
    let finalData = respData;
    
    if (respData && typeof respData === 'object' && 'code' in respData && 'data' in respData) {
      finalData = respData;
    } else {
      finalData = normalizeAnimeListResponse(respData);
    }

    // 在前端根据 is_admin 参数过滤数据
    if (params.is_admin !== undefined) {
      const isAdminFilter = params.is_admin === true || params.is_admin === 'true';
      if (finalData.data && finalData.data.list) {
        finalData.data.list = finalData.data.list.filter(item => {
          // 使用 isAdmin 字段进行过滤
          return item.isAdmin === isAdminFilter;
        });
        // 更新分页信息
        finalData.data.pagination.total = finalData.data.list.length;
        finalData.data.pagination.pages = Math.ceil(finalData.data.list.length / (params.limit || 12));
      }
    }

    return finalData;
  } catch (error) {
    console.error('获取动漫列表失败:', error);
    throw error;
  }
};



// 获取动漫详情 - 根据新接口调整
export const getAnimeDetail = async (id) => {
  try {
    const response = await apiClient.get(`/api/anime/${id}`);
    
    // 直接返回响应数据，因为接口已经使用标准格式
    return response?.data || {
      code: -1,
      message: '未获取到数据',
      data: null
    };
  } catch (error) {
    console.error('获取动漫详情失败:', error);
    
    // 统一错误响应格式
    if (error.response) {
      throw new Error(error.response.data?.message || `请求失败: ${error.response.status}`);
    } else if (error.request) {
      throw new Error('网络连接失败，请检查网络设置');
    } else {
      throw new Error('请求配置错误');
    }
  }
};
/*
// 获取动漫角色列表
export const getAnimeCharacters = async (animeId) => {
  try {
    const response = await apiClient.get(`/api/anime/${animeId}/characters`);
    
    const respData = response?.data;
    if (respData && typeof respData === 'object' && 'code' in respData) {
      return respData;
    }
    
    return {
      code: 0,
      message: 'success',
      data: Array.isArray(respData) ? respData : []
    };
  } catch (error) {
    console.error('获取角色列表失败:', error);
    throw error;
  }
};

// 获取动漫剧集列表
export const getAnimeEpisodes = async (animeId) => {
  try {
    const response = await apiClient.get(`/api/anime/${animeId}/episodes`);
    
    const respData = response?.data;
    if (respData && typeof respData === 'object' && 'code' in respData) {
      return respData;
    }
    
    return {
      code: 0,
      message: 'success',
      data: Array.isArray(respData) ? respData : []
    };
  } catch (error) {
    console.error('获取剧集列表失败:', error);
    throw error;
  }
};

// 获取动漫评论
export const getAnimeComments = async (animeId, params = {}) => {
  try {
    const response = await apiClient.get(`/api/anime/${animeId}/comments`, { params });
    
    const respData = response?.data;
    if (respData && typeof respData === 'object' && 'code' in respData) {
      return respData;
    }
    
    return {
      code: 0,
      message: 'success',
      data: Array.isArray(respData) ? respData : []
    };
  } catch (error) {
    console.error('获取评论失败:', error);
    throw error;
  }
};

// 获取推荐动漫
export const getRecommendations = async (animeId) => {
  try {
    const response = await apiClient.get(`/api/anime/${animeId}/recommendations`);
    
    const respData = response?.data;
    if (respData && typeof respData === 'object' && 'code' in respData) {
      return respData;
    }
    
    return {
      code: 0,
      message: 'success',
      data: Array.isArray(respData) ? respData : []
    };
  } catch (error) {
    console.error('获取推荐列表失败:', error);
    throw error;
  }
};
*/
