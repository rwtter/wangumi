package com.wangumi.android.data.model

data class HealthStatus(val status: String = "unknown") {
    val isHealthy: Boolean = status.equals("ok", ignoreCase = true)
}
