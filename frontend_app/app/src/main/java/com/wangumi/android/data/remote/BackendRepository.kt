package com.wangumi.android.data.remote

import com.wangumi.android.data.model.AnimeCreateRequest
import com.wangumi.android.data.model.AnimeDetailData
import com.wangumi.android.data.model.AnimeDetailResponse
import com.wangumi.android.data.model.AnimeDetailResult
import com.wangumi.android.data.model.AnimeListResult
import com.wangumi.android.data.model.AnimeListResponse
import com.wangumi.android.data.model.HealthStatus
import com.wangumi.android.data.model.LoginRequest
import com.wangumi.android.data.model.Pagination
import com.wangumi.android.data.model.RecommendationResult
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import retrofit2.HttpException
import java.io.IOException
import kotlin.jvm.Volatile

class BackendRepository(
    private val api: WangumiApi = BackendService.api
) {
    @Volatile
    private var accessToken: String? = null
    suspend fun checkHealth(): NetworkResult<HealthStatus> = withContext(Dispatchers.IO) {
        try {
            val status = api.health()
            NetworkResult.Success(HealthStatus(status.status))
        } catch (t: Throwable) {
            NetworkResult.Error(humanReadableMessage(t), t)
        }
    }

    suspend fun login(request: LoginRequest): NetworkResult<Unit> = withContext(Dispatchers.IO) {
        try {
            val response = api.login(request)
            if (!response.access.isNullOrBlank()) {
                accessToken = response.access
                NetworkResult.Success(Unit)
            } else {
                NetworkResult.Error(response.detail ?: "无法登录，请检查凭据")
            }
        } catch (t: Throwable) {
            NetworkResult.Error(humanReadableMessage(t), t)
        }
    }

    suspend fun getAnimeDetail(id: Int): NetworkResult<AnimeDetailResult> =
        withContext(Dispatchers.IO) {
            try {
                val response = api.getAnimeDetail(id)
                val data = response.data ?: return@withContext NetworkResult.Error("未找到番剧")
                NetworkResult.Success(AnimeDetailResult(data))
            } catch (t: Throwable) {
                NetworkResult.Error(humanReadableMessage(t), t)
            }
        }

    suspend fun createAnime(request: AnimeCreateRequest): NetworkResult<Int> =
        withContext(Dispatchers.IO) {
            val token = accessToken ?: return@withContext NetworkResult.Error("请先登录再创建番剧")
            try {
                val response = api.createAnime(request, "Bearer $token")
                if (response.code == 0) {
                    return@withContext NetworkResult.Success(response.data?.id ?: -1)
                }
                NetworkResult.Error(response.message ?: "创建番剧失败")
            } catch (t: Throwable) {
                NetworkResult.Error(humanReadableMessage(t), t)
            }
        }

    suspend fun getRecommendations(
        source: String? = null,
        page: Int = 1,
        limit: Int = 20
    ): NetworkResult<RecommendationResult> = withContext(Dispatchers.IO) {
        try {
            val response = api.getRecommendations(
                authorization = accessToken?.let { "Bearer $it" },
                source = source,
                page = page,
                limit = limit
            )
            NetworkResult.Success(
                RecommendationResult(
                    total = response.count,
                    page = response.page,
                    limit = response.limit,
                    list = response.results
                )
            )
        } catch (t: Throwable) {
            NetworkResult.Error(humanReadableMessage(t), t)
        }
    }

    private fun humanReadableMessage(throwable: Throwable): String = when (throwable) {
        is HttpException -> "后端返回 ${throwable.code()}"
        is IOException -> "无法连接后端，请检查网络或Django服务"
        else -> throwable.message ?: "未知错误"
    }

    suspend fun getAnimeList(
        sort: String,
        categories: List<String>,
        page: Int,
        limit: Int
    ): NetworkResult<AnimeListResult> = withContext(Dispatchers.IO) {
        try {
            val categoryParam = categories.filter { it.isNotBlank() }
                .joinToString(",")
                .ifBlank { null }
            val response = api.getAnimeList(
                sort = sort.takeIf { it.isNotBlank() },
                category = categoryParam,
                page = page,
                limit = limit
            )
            NetworkResult.Success(response.toDomain(sort, categories, page, limit))
        } catch (t: Throwable) {
            NetworkResult.Error(humanReadableMessage(t), t)
        }
    }

    private fun AnimeListResponse.toDomain(
        requestedSort: String,
        requestedCategories: List<String>,
        requestedPage: Int,
        requestedLimit: Int
    ): AnimeListResult {
        val data = this.data
        val pagination = data?.pagination ?: Pagination(
            page = requestedPage,
            limit = requestedLimit,
            total = data?.list?.size ?: 0,
            pages = 0
        )
        val categories = data?.categoryFilter?.takeIf { it.isNotEmpty() } ?: requestedCategories
        return AnimeListResult(
            list = data?.list ?: emptyList(),
            pagination = pagination,
            sortLabel = data?.sort ?: requestedSort,
            categories = categories
        )
    }
}
