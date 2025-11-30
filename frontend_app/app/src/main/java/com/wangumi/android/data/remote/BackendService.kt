package com.wangumi.android.data.remote

import com.google.gson.GsonBuilder
import com.wangumi.android.BuildConfig
import com.wangumi.android.data.model.AnimeCreateRequest
import com.wangumi.android.data.model.AnimeCreateResponse
import com.wangumi.android.data.model.AnimeDetailResponse
import com.wangumi.android.data.model.AnimeListResponse
import com.wangumi.android.data.model.LoginRequest
import com.wangumi.android.data.model.RecommendationResponse
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Query
import retrofit2.http.Path
import retrofit2.http.Header

data class HealthResponse(val status: String = "unknown")

data class LoginResponse(
    val refresh: String? = null,
    val access: String? = null,
    val detail: String? = null
)

interface WangumiApi {
    @GET("health")
    suspend fun health(): HealthResponse

    @POST("login/")
    suspend fun login(@Body request: LoginRequest): LoginResponse

    @GET("anime")
    suspend fun getAnimeList(
        @Query("sort") sort: String? = null,
        @Query("category") category: String? = null,
        @Query("page") page: Int? = null,
        @Query("limit") limit: Int? = null
    ): AnimeListResponse

    @GET("anime/{id}")
    suspend fun getAnimeDetail(@Path("id") id: Int): AnimeDetailResponse

    @POST("anime")
    suspend fun createAnime(
        @Body request: AnimeCreateRequest,
        @Header("Authorization") authorization: String? = null
    ): AnimeCreateResponse

    @GET("recommend_anime/")
    suspend fun getRecommendations(
        @Header("Authorization") authorization: String? = null,
        @Query("source") source: String? = null,
        @Query("page") page: Int? = null,
        @Query("limit") limit: Int? = null
    ): RecommendationResponse
}

object BackendService {
    val api: WangumiApi by lazy {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
        val client = OkHttpClient.Builder()
            .addInterceptor(logging)
            .build()

        val gson = GsonBuilder().setLenient().create()

        Retrofit.Builder()
            .baseUrl(BuildConfig.BACKEND_BASE_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create(gson))
            .build()
            .create(WangumiApi::class.java)
    }
}
