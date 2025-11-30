<template>
  <div class="user-menu" @mouseenter="show = true" @mouseleave="show = false">
    <img
      src="/default-avatar.png"
      alt="User Avatar"
      class="avatar"
    />
    <transition name="fade">
      <div v-if="show" class="menu-panel"> 
        <p class="menu-item" @click="go('/change-password')">修改密码</p>
        <p class="menu-item" @click="go('/change-contact')">修改邮箱 </p>
        <hr />
        <p class="menu-item logout" @click="logout">退出登录</p>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter()
const show = ref(false)

function go(path) {
  console.log('跳转到:', path) // 添加调试日志
  router.push(path)
}

function logout() { 
    // 清除本地 token
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')

    // 触发登出事件，通知App.vue更新状态
    window.dispatchEvent(new CustomEvent('user-logged-out'))
    
    // 登出成功后跳转到登录页
    setTimeout(() => {
      router.push('/login')
    }, 1000) 
}
</script>

<style scoped>
.user-menu {
  position: relative;
  display: inline-block;
  cursor: pointer;
}
.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2px solid #ddd;
  object-fit: cover;
}
.menu-panel {
  position: absolute;
  top: 52px;
  right: 0;
  width: 160px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  z-index: 1000;
  padding: 8px 0;
}
.menu-item {
  padding: 10px 16px;
  font-size: 14px;
  color: #333;
  transition: background-color 0.2s;
}
.menu-item:hover {
  background-color: #f5f5f5;
}
.logout {
  color: #e74c3c;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
