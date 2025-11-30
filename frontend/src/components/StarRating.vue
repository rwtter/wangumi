<template>
  <div class="star-rating" :class="size">
    <div class="stars-container">
      <div
        v-for="star in 5"
        :key="star"
        class="star-wrapper"
        @click="handleStarClick(star)"
        @mousemove="handleMouseMove($event, star)"
        @mouseleave="handleMouseLeave"
      >
        <!-- 背景星星 -->
        <i class="fas fa-star star-bg"></i>

        <!-- 填充星星 (根据rating决定宽度) -->
        <i
          class="fas fa-star star-fill"
          :style="{ width: getStarFillWidth(star) }"
        ></i>
      </div>
    </div>

    <div class="rating-text">
      <span v-if="hoverRating > 0 && !readonly" class="hover-score">{{ hoverRating }}</span>
      <span v-else class="current-score">{{ displayScore }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Number,
    default: 0
  },
  readonly: {
    type: Boolean,
    default: false
  },
  size: {
    type: String,
    default: 'medium' // 'small', 'medium', 'large'
  }
})

const emit = defineEmits(['update:modelValue'])

const hoverRating = ref(0)

// 显示分数
const displayScore = computed(() => {
  return props.modelValue > 0 ? props.modelValue : '未评分'
})

// 获取每颗星的填充宽度
const getStarFillWidth = (starIndex) => {
  const rating = hoverRating.value || props.modelValue || 0
  const score = rating / 2 // 转换为5星制

  if (score >= starIndex) {
    return '100%'
  } else if (score >= starIndex - 0.5) {
    return '50%'
  } else {
    return '0%'
  }
}

// 处理星星点击
const handleStarClick = (starIndex) => {
  if (props.readonly) return

  // 如果点击的是当前评分，则清除评分
  if (props.modelValue === starIndex * 2) {
    emit('update:modelValue', 0)
  } else {
    // 使用hoverRating作为新评分
    emit('update:modelValue', hoverRating.value)
  }
}

// 处理鼠标移动（半星效果）
const handleMouseMove = (event, starIndex) => {
  if (props.readonly) return

  const rect = event.currentTarget.getBoundingClientRect()
  const x = event.clientX - rect.left
  const isLeftHalf = x < rect.width / 2

  // 计算10分制评分
  hoverRating.value = isLeftHalf ? (starIndex * 2 - 1) : (starIndex * 2)
}

// 鼠标离开
const handleMouseLeave = () => {
  hoverRating.value = 0
}
</script>

<style scoped>
.star-rating {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stars-container {
  display: flex;
  gap: 4px;
}

.star-wrapper {
  position: relative;
  width: 28px;
  height: 28px;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.star-wrapper:hover {
  transform: scale(1.1);
}

.star-rating.readonly .star-wrapper {
  cursor: default;
}

.star-rating.readonly .star-wrapper:hover {
  transform: none;
}

.star-bg,
.star-fill {
  position: absolute;
  top: 0;
  left: 0;
  font-size: 28px;
  pointer-events: none;
}

.star-bg {
  color: #e0e0e0;
}

.star-fill {
  color: #ffd166;
  overflow: hidden;
  transition: width 0.2s ease;
  text-shadow: 0 0 8px rgba(255, 209, 102, 0.6);
}

.rating-text {
  min-width: 60px;
  text-align: center;
}

.hover-score {
  color: #ff6b9d;
  font-size: 20px;
  font-weight: bold;
  text-shadow: 1px 1px 0 #ffc2d9;
}

.current-score {
  color: #666;
  font-size: 16px;
  font-weight: 600;
}

/* 尺寸变体 */
.star-rating.small .star-wrapper {
  width: 20px;
  height: 20px;
}

.star-rating.small .star-bg,
.star-rating.small .star-fill {
  font-size: 20px;
}

.star-rating.large .star-wrapper {
  width: 36px;
  height: 36px;
}

.star-rating.large .star-bg,
.star-rating.large .star-fill {
  font-size: 36px;
}

.star-rating.large .hover-score {
  font-size: 24px;
}

.star-rating.large .current-score {
  font-size: 18px;
}

/* 只读模式的样式调整 */
.star-rating.readonly .stars-container {
  gap: 2px;
}

.star-rating.readonly .star-wrapper {
  width: 24px;
  height: 24px;
}

.star-rating.readonly .star-bg,
.star-rating.readonly .star-fill {
  font-size: 24px;
}
</style>
