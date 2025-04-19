import Vue from 'vue'
import VueRouter from 'vue-router'
import store from '@/store'

Vue.use(VueRouter)

// 路由懒加载
const Home = () => import('@/views/Home.vue')
const Login = () => import('@/views/Login.vue')
const Register = () => import('@/views/Register.vue')
const Layout = () => import('@/views/layout/Layout.vue')
const Dashboard = () => import('@/views/dashboard/Dashboard.vue')
const DetectionCreate = () => import('@/views/detection/Create.vue')
const DetectionHistory = () => import('@/views/detection/History.vue')
const DetectionDetail = () => import('@/views/detection/Detail.vue')
const Profile = () => import('@/views/user/Profile.vue')
const NotFound = () => import('@/views/NotFound.vue')

// 管理员相关组件
const AdminLayout = () => import('@/views/admin/AdminLayout.vue')
const AdminDashboard = () => import('@/views/admin/Dashboard.vue')
const AdminUsers = () => import('@/views/admin/Users.vue')
const AdminSettings = () => import('@/views/admin/Settings.vue')
const DetectionStatistics = () => import('@/views/admin/DetectionStatistics.vue')
// 系统日志页面 - 懒加载
const SystemLogs = () => import('@/views/admin/SystemLogs.vue')

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { title: '首页', noAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { title: '登录', noAuth: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { title: '注册', noAuth: true }
  },
  {
    path: '/dashboard',
    component: Layout,
    redirect: '/dashboard/index',
    children: [
      {
        path: 'index',
        name: 'Dashboard',
        component: Dashboard,
        meta: { title: '仪表盘', icon: 'el-icon-data-analysis' }
      },
      {
        path: 'detection/create',
        name: 'DetectionCreate',
        component: DetectionCreate,
        meta: { title: '新闻检测', icon: 'el-icon-search' }
      },
      {
        path: 'detection/history',
        name: 'DetectionHistory',
        component: DetectionHistory,
        meta: { title: '检测历史', icon: 'el-icon-time' }
      },
      {
        path: 'detection/detail/:id',
        name: 'DetectionDetail',
        component: DetectionDetail,
        meta: { title: '检测详情', hideInMenu: true }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: Profile,
        meta: { title: '个人中心', icon: 'el-icon-user' }
      }
    ]
  },
  // 添加管理员路由
  {
    path: '/admin',
    component: AdminLayout,
    redirect: '/admin/dashboard',
    meta: { requiresAdmin: true },
    children: [
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: AdminDashboard,
        meta: { title: '控制面板' }
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: AdminUsers,
        meta: { title: '用户列表' }
      },
      {
        path: 'settings',
        name: 'AdminSettings',
        component: AdminSettings,
        meta: { title: '系统设置' }
      },
      {
        path: 'detection/list',
        name: 'AdminDetectionList',
        component: DetectionHistory,
        meta: { title: '检测列表' }
      },
      {
        path: 'detection/detail/:id',
        name: 'AdminDetectionDetail',
        component: DetectionDetail,
        meta: { title: '检测详情', hideInMenu: true }
      },
      {
        path: 'detection-stats',
        name: 'AdminDetectionStats',
        component: DetectionStatistics,
        meta: { title: '检测统计' }
      },
      {
        path: 'logs',
        name: 'AdminLogs',
        component: SystemLogs,
        meta: { title: '系统日志' }
      }
    ]
  },
  {
    path: '/404',
    name: 'NotFound',
    component: NotFound,
    meta: { title: '页面不存在', noAuth: true, hideInMenu: true }
  },
  // 重定向到404
  { path: '*', redirect: '/404' }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes,
  // 页面切换时滚动到顶部
  scrollBehavior() {
    return { x: 0, y: 0 }
  }
})

// 避免重复导航错误
const originalPush = VueRouter.prototype.push
VueRouter.prototype.push = function push(location) {
  return originalPush.call(this, location).catch(err => {
    if (err.name !== 'NavigationDuplicated') throw err
  })
}

// 全局前置守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 虚假新闻检测系统` : '虚假新闻检测系统'
  
  // 获取token状态
  const token = store.getters.token
  const isAdmin = store.getters.isAdmin
  
  // 首页特殊处理：已登录用户访问首页时自动跳转到仪表盘
  if (to.path === '/' && token) {
    next({ path: '/dashboard/index' })
    return
  }
  
  // 管理员页面检查
  if (to.matched.some(record => record.meta.requiresAdmin)) {
    if (!token) {
      next({ path: '/login', query: { redirect: to.fullPath } })
      return
    }
    
    if (!isAdmin) {
      next({ path: '/404' })
      return
    }
    
    // 管理员有权限访问，正常通过
    next()
    return
  }
  
  // 不需要登录的页面
  if (to.meta.noAuth) {
    next()
    return
  }
  
  // 判断是否已登录
  if (!token) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }
  
  next()
})

export default router
