package com.wangumi.android.data.model

import com.google.gson.annotations.SerializedName

data class RecommendationResponse(
    val count: Int = 0,
    val page: Int = 1,
    val limit: Int = 0,
    val results: List<RecommendationItem> = emptyList()
)

data class RecommendationItem(
    val id: Int = 0,
    val title: String? = null,
    val reason: String? = null,
    val score: Double? = null,
    val cover: String? = null,
    val summary: String? = null,
    val rating: Double? = null,
    val popularity: Int? = null,
    @SerializedName("total_episodes")
    val totalEpisodes: Int? = null,
    @SerializedName("episodes_released")
    val episodesReleased: Int? = null,
    val genres: List<String>? = null,
    @SerializedName("release_date")
    val releaseDate: String? = null
)

data class RecommendationResult(
    val total: Int,
    val page: Int,
    val limit: Int,
    val list: List<RecommendationItem>
)
