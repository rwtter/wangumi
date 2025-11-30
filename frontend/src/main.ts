import { createApp } from 'vue'
import App from './App.vue'
import{ createRouter, createWebHistory }from 'vue-router'

import AnimeList from "@/components/AnimeList.vue"
import Recommend from "@/components/Recommend.vue"
import PersonalSpace from "@/components/PersonalSpace.vue"
import AnimeDetailView from "@/components/AnimeDetailView.vue"
import Login from "@/components/LoginPage.vue"
import Register from "@/components/RegisterForm.vue"
import ForgotPassword from "@/components/ForgotPassword.vue";
import ChangeContact from './components/ChangeContact.vue'
import ChangePassword from './components/ChangePassword.vue'
import ItemList from './components/ItemList.vue'
import ItemCreate from './components/ItemCreate.vue'
import ItemDetail from './components/ItemDetail.vue'
import EpisodeDetail from './components/EpisodeDetail.vue'

//1.配置路由规则
const routes =[
    {path:"/",redirect:"animelist"},
    {path:"/animelist",component:AnimeList},
    {path:"/recommend",component:Recommend},
    {path:"/personal",component:PersonalSpace},
    {path:"/anime/:id",component:AnimeDetailView},
    {path:"/login",component:Login},
    {path:"/register",component:Register},
    {path:"/forgot-password", component: ForgotPassword },
    {path:"/change-contact", component: ChangeContact },
    {path:"/change-password", component: ChangePassword },
    // 条目相关路由
    {path:"/items", component: ItemList},
    {path:"/items/create", component: ItemCreate},
    {path:"/item/:id", component: ItemDetail},
    // 单集详情页路由
    {path:"/episode/:episodeId", component: EpisodeDetail, props: true}
]
//2.创建路由器
const router =createRouter({
    history:createWebHistory(),//路由工作模式 支持回退
    routes
})
//3.加载路由器
let app=createApp(App)
app.use(router)
app.mount('#app')

// 调试：确认环境变量（置于所有 import 之后，避免某些工具链/规则报错）
console.log('VITE_API_BASE_URL =', import.meta.env.VITE_API_BASE_URL)
