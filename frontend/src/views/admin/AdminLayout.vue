<template>
  <div class="admin-layout">
    <el-container>
      <el-aside width="220px">
        <div class="admin-logo">
          <h2>后台管理系统</h2>
        </div>
        <el-menu
          :default-active="$route.path"
          class="admin-menu"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
          router
        >
          <el-menu-item index="/admin/dashboard">
            <i class="el-icon-s-data"></i>
            <span>控制面板</span>
          </el-menu-item>
          
          <el-submenu index="users">
            <template slot="title">
              <i class="el-icon-user"></i>
              <span>用户管理</span>
            </template>
            <el-menu-item index="/admin/users">
              <i class="el-icon-user-solid"></i>
              <span>用户列表</span>
            </el-menu-item>
            <el-menu-item index="/admin/users/create">
              <i class="el-icon-plus"></i>
              <span>添加用户</span>
            </el-menu-item>
          </el-submenu>
          
          <el-submenu index="detections">
            <template slot="title">
              <i class="el-icon-search"></i>
              <span>检测管理</span>
            </template>
            <el-menu-item index="/admin/detection/list">
              <i class="el-icon-document"></i>
              <span>检测列表</span>
            </el-menu-item>
            <el-menu-item index="/admin/detection-stats">
              <i class="el-icon-data-analysis"></i>
              <span>统计分析</span>
            </el-menu-item>
          </el-submenu>
          
          <el-submenu index="system">
            <template slot="title">
              <i class="el-icon-setting"></i>
              <span>系统设置</span>
            </template>
            <el-menu-item index="/admin/settings">
              <i class="el-icon-s-tools"></i>
              <span>参数设置</span>
            </el-menu-item>
            <el-menu-item index="/admin/logs">
              <i class="el-icon-notebook-2"></i>
              <span>系统日志</span>
            </el-menu-item>
          </el-submenu>
        </el-menu>
      </el-aside>
      
      <el-container>
        <el-header>
          <div class="admin-header">
            <div class="breadcrumb">
              <el-breadcrumb separator="/">
                <el-breadcrumb-item :to="{ path: '/admin/dashboard' }">首页</el-breadcrumb-item>
                <el-breadcrumb-item v-for="(item, index) in breadcrumbs" :key="index">
                  {{ item }}
                </el-breadcrumb-item>
              </el-breadcrumb>
            </div>
            
            <div class="user-info">
              <el-dropdown trigger="click" @command="handleCommand">
                <span class="el-dropdown-link">
                  <el-avatar :size="32" icon="el-icon-user-solid"></el-avatar>
                  <span class="username">{{ currentUser.username }}</span>
                  <i class="el-icon-arrow-down el-icon--right"></i>
                </span>
                <el-dropdown-menu slot="dropdown">
                  <el-dropdown-item command="profile">个人资料</el-dropdown-item>
                  <el-dropdown-item command="settings">偏好设置</el-dropdown-item>
                  <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </el-dropdown>
            </div>
          </div>
        </el-header>
        
        <el-main>
          <router-view />
        </el-main>
        
        <el-footer>
          <div class="admin-footer">
            <p>© {{ new Date().getFullYear() }} 虚假新闻检测系统 - 后台管理</p>
          </div>
        </el-footer>
      </el-container>
    </el-container>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'AdminLayout',
  data() {
    return {
      breadcrumbs: []
    }
  },
  computed: {
    ...mapGetters(['currentUser'])
  },
  watch: {
    $route: {
      handler: function(route) {
        this.updateBreadcrumbs(route)
      },
      immediate: true
    }
  },
  methods: {
    handleCommand(command) {
      if (command === 'logout') {
        this.$store.dispatch('user/logout')
          .then(() => {
            this.$router.push('/login')
            this.$message.success('已成功退出登录')
          })
      } else if (command === 'profile') {
        this.$router.push('/admin/profile')
      } else if (command === 'settings') {
        this.$router.push('/admin/settings')
      }
    },
    
    updateBreadcrumbs(route) {
      const paths = route.path.split('/').filter(Boolean)
      const breadcrumbs = []
      
      if (paths.length > 1 && paths[0] === 'admin') {
        for (let i = 1; i < paths.length; i++) {
          let path = paths[i].charAt(0).toUpperCase() + paths[i].slice(1)
          breadcrumbs.push(this.formatBreadcrumb(path))
        }
      }
      
      this.breadcrumbs = breadcrumbs
    },
    
    formatBreadcrumb(path) {
      const breadcrumbMap = {
        'Dashboard': '控制面板',
        'Users': '用户列表',
        'Create': '添加用户',
        'Detections': '检测列表',
        'Detection-stats': '统计分析',
        'Settings': '系统设置',
        'Logs': '系统日志',
        'Profile': '个人资料'
      }
      
      return breadcrumbMap[path] || path
    }
  }
}
</script>

<style lang="scss" scoped>
.admin-layout {
  min-height: 100vh;
  
  .el-container {
    min-height: 100vh;
  }
  
  .el-aside {
    background-color: #304156;
    color: white;
    height: 100vh;
    position: fixed;
    left: 0;
    top: 0;
    z-index: 10;
  }
  
  .el-container:nth-child(2) {
    margin-left: 220px;
  }
  
  .admin-logo {
    height: 60px;
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: #263445;
    
    h2 {
      color: white;
      margin: 0;
      font-size: 18px;
    }
  }
  
  .admin-menu {
    border-right: none;
  }
  
  .el-header {
    background-color: white;
    color: #333;
    box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
    position: relative;
    z-index: 9;
    padding: 0;
    
    .admin-header {
      height: 60px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0 20px;
      
      .breadcrumb {
        flex: 1;
      }
      
      .user-info {
        display: flex;
        align-items: center;
        
        .el-dropdown-link {
          display: flex;
          align-items: center;
          cursor: pointer;
          
          .username {
            margin: 0 10px;
          }
        }
      }
    }
  }
  
  .el-main {
    background-color: #f0f2f5;
    padding: 20px;
  }
  
  .el-footer {
    text-align: center;
    color: #999;
    padding: 20px;
    background-color: white;
  }
}
</style> 