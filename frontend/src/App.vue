<template>
  <div class="anime-website">
    <header class="header">
      <nav class="nav-container">
        <div class="logo" @click="goHome">Wangumi</div>
        
        <ul class="nav-links">
          <li v-for="item in navItems" :key="item.id">
            <RouterLink 
              :to="item.to"
              :class="{ active: activeNav === item.id }">
              {{ item.text }}
            </RouterLink>
          </li>
        </ul>

        <div class="user-actions">
          <!-- 未登录 -->
          <template v-if="!isLoggedIn">
            <button class="login-btn" @click="handleLogin">注册/登录</button>
          </template>

          <!-- 已登录：显示独立的 UserMenu 组件 -->
          <template v-else>
            <UserMenu />
            </template>
        </div>
      </nav>
    </header>
    
    <main class="main-content">
      <RouterView/>
    </main>
  </div>
</template>

<script>
import UserMenu from "@/components/UserMenu.vue";
 
export default {
  name: 'AnimeWebsite',
  components: { UserMenu },
  data() {
    return {
      navItems: [
        { id: 'anime-list', text: '番剧列表', to: '/animelist' },
        { id: 'recommend', text: '推荐', to: '/recommend' },
        { id: 'personal-space', text: '个人空间', to: '/personal' }
      ],
      isLoggedIn: false,
    }
  },
  computed: {
    activeNav() {
      // 根据当前路由自动设置激活状态
      const routeMap = {
        '/animelist': 'anime-list',
        '/recommend': 'recommend',
        '/personal': 'personal-space'
      };
      return routeMap[this.$route.path] || 'anime-list';
    }
  },
  methods: {
    goHome() {
      this.$router.push('/animelist');
      console.log('返回首页');
    },
    handleLogin(event) {
      this.$router.push('/login');
      console.log('跳转到登录页面');
    }
  },
  mounted() {
    // 初始化检查
    this.isLoggedIn = !!localStorage.getItem('access_token')

    // 监听登录事件
    window.addEventListener('user-logged-in', () => {
      this.isLoggedIn = true
    })

    // 监听登出事件（如果 UserMenu 调用了 handleLogout）
    window.addEventListener('user-logged-out', () => {
      this.isLoggedIn = false
    })
  },
  beforeUnmount() {
    window.removeEventListener('user-logged-in', () => {})
    window.removeEventListener('user-logged-out', () => {})
    },
}
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.anime-website {
  font-family: 'Mochiy Pop One', 'Arial Rounded MT Bold', sans-serif;
  background: linear-gradient(135deg, #ffcfe6, #c2e9fb);
  min-height: 100vh;
  color: #333;
}

.header {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  padding: 15px 30px;
  position: sticky;
  top: 0;
  z-index: 1000;
  border-bottom: 3px solid #ff6b9d;
}

.nav-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
}

.logo {
  display: flex;
  align-items: center;
  font-size: 28px;
  font-weight: bold;
  color: #ff6b9d;
  text-shadow: 2px 2px 0 #ffc2d9;
  transition: all 0.3s ease;
  cursor: pointer;
}

.logo:hover {
  transform: scale(1.05);
  text-shadow: 3px 3px 0 #ffc2d9, 5px 5px 5px rgba(0, 0, 0, 0.1);
}

.logo i {
  margin-right: 10px;
  font-size: 32px;
}

.nav-links {
  display: flex;
  list-style: none;
  gap: 30px;
}

.nav-links li {
  position: relative;
}

.nav-links a {
  text-decoration: none;
  color: #5a5a5a;
  font-size: 18px;
  padding: 8px 15px;
  border-radius: 20px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  display: block;
}

.nav-links a:before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.6), transparent);
  transition: all 0.5s ease;
}

.nav-links a:hover:before {
  left: 100%;
}

.nav-links a:hover {
  color: #ff6b9d;
  background: rgba(255, 107, 157, 0.1);
  transform: translateY(-3px);
  box-shadow: 0 5px 15px rgba(255, 107, 157, 0.3);
}

.nav-links a.active {
  color: #ff6b9d;
  background: rgba(255, 107, 157, 0.15);
}

.user-actions {
  display: flex;
  align-items: center;
}

.login-btn {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 25px;
  font-family: inherit;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 10px rgba(255, 107, 157, 0.4);
}

.login-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 15px rgba(255, 107, 157, 0.6);
}

.login-btn:active {
  transform: translateY(0);
}

.main-content {
  max-width: 1500px;
  margin: 0 auto;
  padding: 0px 0px;
}

.login-container{
  background-color: #ffffff;  /* 白色背景 */
  width: 500px;               /* 调整宽度 */
  padding: 40px 32px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.register-container {
  background-color: #ffffff;  /* 白色背景 */
  width: 500px;               /* 调整宽度 */
  padding: 40px 32px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .nav-container {
    flex-direction: column;
    gap: 15px;
  }
  
  .nav-links {
    gap: 15px;
  }
  
  .logo {
    font-size: 24px;
  }
}
</style>
