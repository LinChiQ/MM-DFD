<template>
  <el-container class="app-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapsed ? '64px' : '240px'" class="sidebar-container" :class="{ 'collapsed': isCollapsed }">
      <div class="logo">
        <el-image :src="logoSrc" alt="Logo" class="logo-image"></el-image>
        <span class="logo-text" v-show="!isCollapsed">MM-DFD系统</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapsed"
        router
        :collapse-transition="false"
        background-color="#2b2d42"
        text-color="#e9ecef"
        active-text-color="#4cc9f0"
        class="sidebar-menu"
      >
        <el-menu-item v-for="item in visibleRoutes" :key="item.path" :index="'/dashboard/' + item.path">
          <i :class="item.meta ? item.meta.icon : 'el-icon-document'"></i>
          <span slot="title">{{ item.meta ? item.meta.title : item.name }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container class="main-container">
      <!-- 头部 -->
      <el-header class="app-header">
        <div class="header-left">
          <i 
            :class="isCollapsed ? 'el-icon-s-unfold' : 'el-icon-s-fold'" 
            class="toggle-btn" 
            @click="toggleSidebar"
          ></i>
        </div>
        <div class="header-right">
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="user-info">
              <el-avatar :size="32" icon="el-icon-user"></el-avatar>
              <span class="username" v-if="!isSmallScreen">{{ username }}</span>
              <i class="el-icon-arrow-down"></i>
            </div>
            <el-dropdown-menu slot="dropdown">
              <el-dropdown-item command="profile">
                <i class="el-icon-user-solid"></i> 个人中心
              </el-dropdown-item>
              <el-dropdown-item command="logout">
                <i class="el-icon-switch-button"></i> 退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </el-dropdown>
        </div>
      </el-header>
      
      <!-- 主体内容 -->
      <el-main class="app-main">
        <transition name="fade" mode="out-in">
          <router-view />
        </transition>
      </el-main>
      
      <!-- 页脚 -->
      <el-footer height="40px" class="app-footer">
        <span>© 2025 多模态深度学习社交媒体虚假新闻检测系统 (MM-DFD)</span>
      </el-footer>
    </el-container>
  </el-container>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'LayoutView',
  data() {
    return {
      isCollapsed: false,
      isSmallScreen: false
    }
  },
  computed: {
    ...mapGetters(['user']),
    activeMenu() {
      const { path } = this.$route
      if (path.startsWith('/dashboard/')) {
        return path
      }
      return '/dashboard/index'
    },
    routes() {
      return this.$router.options.routes.find(route => route.path === '/dashboard').children.filter(route => !route.meta || !route.meta.hideInMenu)
    },
    visibleRoutes() {
      return this.$router.options.routes.find(route => route.path === '/dashboard').children.filter(route => !route.meta || !route.meta.hideInMenu)
    },
    username() {
      return this.user.username || '用户'
    },
    logoSrc() {
      try {
        return require('@/assets/logo.svg')
      } catch (e) {
        return this.$defaultLogo || ''
      }
    }
  },
  methods: {
    toggleSidebar() {
      this.isCollapsed = !this.isCollapsed
    },
    handleCommand(command) {
      if (command === 'logout') {
        this.$store.dispatch('user/logout')
      } else if (command === 'profile') {
        this.$router.push('/dashboard/profile')
      }
    },
    handleResize() {
      this.isSmallScreen = window.innerWidth < 768
      if (window.innerWidth < 992 && !this.isCollapsed) {
        this.isCollapsed = true
      }
    }
  },
  mounted() {
    this.handleResize()
    window.addEventListener('resize', this.handleResize)
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.handleResize)
  }
}
</script>

<style lang="scss" scoped>
@import "@/assets/css/variables.scss";

.app-container {
  height: 100vh;
  overflow: hidden;
}

.sidebar-container {
  background-color: #2b2d42;
  color: #fff;
  transition: width $transition-base;
  position: relative;
  z-index: 10;
  overflow-x: hidden;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

.main-container {
  transition: margin-left $transition-base;
  position: relative;
  min-height: 100%;
  background: $background-color;
}

.logo {
  height: $header-height;
  display: flex;
  align-items: center;
  padding: 0 15px;
  background-color: #242635;
  overflow: hidden;
}

.logo-image {
  width: 32px;
  height: 32px;
  margin-right: 10px;
  transition: $transition-base;
}

.logo-text {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  white-space: nowrap;
  transition: opacity 0.3s;
}

.sidebar-menu {
  border-right: none;
  &::v-deep .el-menu-item {
    height: 50px;
    line-height: 50px;
    &.is-active {
      background-color: rgba($primary-color, 0.1) !important;
      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 4px;
        background-color: $primary-color;
      }
    }
    &:hover {
      background-color: rgba(255, 255, 255, 0.05) !important;
    }
  }
}

.app-header {
  background-color: white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: $header-height;
  position: relative;
  z-index: 9;
}

.toggle-btn {
  cursor: pointer;
  font-size: 20px;
  color: $regular-font-color;
  transition: $transition-base;
  padding: 10px;
  border-radius: $border-radius-small;
  
  &:hover {
    color: $primary-color;
    background-color: rgba($primary-color, 0.1);
  }
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: $border-radius-base;
  transition: $transition-base;
  
  &:hover {
    background-color: rgba($primary-color, 0.05);
  }
  
  .username {
    margin: 0 10px;
    font-weight: 500;
  }
}

.app-main {
  padding: 20px;
  overflow-y: auto;
  min-height: calc(100vh - #{$header-height} - 40px);
}

.app-footer {
  text-align: center;
  background-color: #fff;
  color: $secondary-font-color;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 -1px 4px rgba(0, 0, 0, 0.03);
}

@media (max-width: $md) {
  .app-main {
    padding: 15px;
  }
}
</style> 