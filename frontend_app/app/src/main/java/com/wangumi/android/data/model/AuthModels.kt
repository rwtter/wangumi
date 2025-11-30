package com.wangumi.android.data.model

data class LoginRequest(
    val username: String,
    val password: String
)

data class TokenPair(
    val access: String?,
    val refresh: String?
)
