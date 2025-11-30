package com.wangumi.android.data.remote

sealed interface NetworkResult<out T> {
    data class Success<T>(val data: T) : NetworkResult<T>
    data class Error(val message: String, val cause: Throwable? = null) : NetworkResult<Nothing>
    data object Loading : NetworkResult<Nothing>
}

inline fun <T> runCatchingNetwork(block: () -> T): NetworkResult<T> =
    try {
        NetworkResult.Success(block())
    } catch (t: Throwable) {
        NetworkResult.Error(t.message ?: "Unknown error", t)
    }
