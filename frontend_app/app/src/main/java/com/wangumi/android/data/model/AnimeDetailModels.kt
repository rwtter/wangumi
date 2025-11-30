package com.wangumi.android.data.model

import com.google.gson.annotations.SerializedName

data class AnimeDetailResponse(
    val code: Int = -1,
    val message: String? = null,
    val data: AnimeDetailData? = null
)

data class AnimeDetailData(
    val basic: AnimeBasicInfo? = null,
    val meta: AnimeMetaInfo? = null,
    val relations: AnimeRelationInfo? = null,
    val comments: CommentList? = null
)

data class AnimeBasicInfo(
    val id: Int,
    val title: String?,
    @SerializedName("titleJapanese")
    val titleJapanese: String?,
    val cover: String?,
    val rating: Double?,
    val summary: String?
)

data class AnimeMetaInfo(
    val category: List<String>?,
    val status: String?,
    val episodes: Int?,
    val releaseDate: String?,
    val updateProgress: String?,
    val createdBy: String?,
    val createdAt: String?,
    @SerializedName("isAdmin")
    val isAdmin: Boolean?
)

data class AnimeRelationInfo(
    val characters: List<AnimeCharacterInfo>?,
    val staff: List<AnimeStaffInfo>?
)

data class AnimeCharacterInfo(
    val name: String?,
    val avatar: String?,
    val voiceActors: List<String>?
)

data class AnimeStaffInfo(
    val role: String?,
    val name: String?,
    val character: String?
)

data class CommentList(
    val list: List<CommentInfo>?
)

data class CommentInfo(
    val user: String?,
    val content: String?,
    @SerializedName("createdAt")
    val createdAt: String?
)

data class AnimeDetailResult(
    val data: AnimeDetailData
)

data class AnimeCreateRequest(
    val title: String,
    val title_cn: String?,
    val description: String?,
    val genres: List<String>?,
    val release_date: String?,
    val status: String?,
    val total_episodes: Int?,
    val cover_url: String?
)

data class AnimeCreateResponse(
    val code: Int,
    val message: String?,
    val data: AnimeCreateResult?
)

data class AnimeCreateResult(
    val id: Int?,
    val detailUrl: String?
)
