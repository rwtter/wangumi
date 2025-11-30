package com.wangumi.android.data.model

import com.google.gson.annotations.SerializedName

data class AnimeListResponse(
    val code: Int = -1,
    val message: String? = null,
    val data: AnimeListData? = null
)

data class AnimeListData(
    val list: List<AnimeSummary> = emptyList(),
    val pagination: Pagination? = null,
    val sort: String? = null,
    @SerializedName("category_filter")
    val categoryFilter: List<String>? = null
)

data class Pagination(
    val page: Int = 1,
    val limit: Int = 20,
    val total: Int = 0,
    val pages: Int = 0
)

data class AnimeSummary(
    val id: Int = 0,
    val title: String? = null,
    val cover: String? = null,
    val rating: Double? = null,
    val popularity: Int? = null,
    val summary: String? = null,
    val time: String? = null,
    val category: List<String>? = null,
    @SerializedName("isAdmin")
    val isAdmin: Boolean? = null
)

data class AnimeListResult(
    val list: List<AnimeSummary>,
    val pagination: Pagination,
    val sortLabel: String,
    val categories: List<String>
)
