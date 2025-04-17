<template>
  <div class="login-container">
    <div class="login-content">
      <div class="login-card">
        <div class="logo-container">
          <el-image :src="logoSrc" alt="Logo" class="logo"></el-image>
          <h2 class="title">多模态虚假新闻检测系统</h2>
        </div>
        
        <el-form ref="loginForm" :model="loginForm" :rules="loginRules" class="login-form">
          <el-form-item prop="username">
            <el-input 
              v-model="loginForm.username" 
              prefix-icon="el-icon-user" 
              placeholder="用户名"
              class="custom-input"
              @keyup.enter.native="handleLogin"
            />
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input 
              v-model="loginForm.password" 
              prefix-icon="el-icon-lock" 
              type="password" 
              placeholder="密码"
              class="custom-input"
              @keyup.enter.native="handleLogin"
            />
          </el-form-item>
          
          <el-button 
            :loading="loading" 
            type="primary" 
            class="login-button" 
            @click="handleLogin"
          >
            登 录
          </el-button>
          
          <div class="login-options">
            <span class="register-link" @click="goToRegister">注册账号</span>
          </div>
        </el-form>
      </div>
    </div>
    <div class="login-background">
      <div class="bg-decoration bg-decoration-1"></div>
      <div class="bg-decoration bg-decoration-2"></div>
      <div class="bg-decoration bg-decoration-3"></div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LoginView',
  data() {
    return {
      loginForm: {
        username: '',
        password: ''
      },
      loginRules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, message: '密码长度不能小于6个字符', trigger: 'blur' }
        ]
      },
      loading: false
    }
  },
  computed: {
    logoSrc() {
      try {
        return require('@/assets/logo.svg')
      } catch (e) {
        return this.$defaultLogo || ''
      }
    }
  },
  methods: {
    handleLogin() {
      this.$refs.loginForm.validate(valid => {
        if (valid) {
          this.loading = true
          this.$store.dispatch('user/login', this.loginForm)
            .then(() => {
              this.$message.success('登录成功')
              // 获取用户信息
              return this.$store.dispatch('user/getUserInfo')
            })
            .then(() => {
              // 重定向到仪表盘或指定页面
              const redirect = this.$route.query.redirect || '/dashboard/index'
              this.$router.push(redirect)
            })
            .catch(error => {
              console.error('登录失败:', error)
              this.$message.error('登录失败: ' + (error.response?.data?.detail || '用户名或密码错误'))
            })
            .finally(() => {
              this.loading = false
            })
        } else {
          return false
        }
      })
    },
    goToRegister() {
      this.$router.push('/register')
    }
  }
}
</script>

<style lang="scss" scoped>
@import "@/assets/css/variables.scss";

.login-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.login-content {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  position: relative;
  z-index: 2;
}

.login-card {
  width: 400px;
  padding: 40px;
  background-color: rgba(255, 255, 255, 0.95);
  border-radius: $border-radius-large;
  box-shadow: $box-shadow-base;
  backdrop-filter: blur(10px);
  animation: fadeIn 0.6s ease-out;
}

.logo-container {
  text-align: center;
  margin-bottom: 30px;
}

.logo {
  width: 80px;
  height: 80px;
  transition: transform 0.3s;
  
  &:hover {
    transform: scale(1.05);
  }
}

.title {
  color: $main-font-color;
  margin-top: 16px;
  font-weight: 600;
  font-size: 24px;
}

.login-form {
  margin-top: 30px;
}

.custom-input {
  :deep(.el-input__inner) {
    height: 50px;
    border-radius: $border-radius-base;
    border: 1px solid $border-light-color;
    transition: all 0.3s;
    
    &:hover, &:focus {
      border-color: $primary-color;
      box-shadow: 0 0 0 2px rgba($primary-color, 0.2);
    }
  }
}

.login-button {
  width: 100%;
  margin-top: 24px;
  height: 50px;
  border-radius: $border-radius-base;
  font-size: 16px;
  font-weight: 500;
  background: linear-gradient(90deg, $primary-color, $info-color);
  border: none;
  transition: transform 0.3s, box-shadow 0.3s;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba($primary-color, 0.4);
  }
  
  &:active {
    transform: translateY(0);
  }
}

.login-options {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

.register-link {
  color: $primary-color;
  cursor: pointer;
  transition: color 0.3s;
  font-weight: 500;

  &:hover {
    color: darken($primary-color, 10%);
    text-decoration: underline;
  }
}

.login-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.bg-decoration {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba($primary-color, 0.6), rgba($info-color, 0.6));
  opacity: 0.1;
  filter: blur(60px);
}

.bg-decoration-1 {
  width: 600px;
  height: 600px;
  top: -100px;
  right: -100px;
  animation: float 10s ease-in-out infinite;
}

.bg-decoration-2 {
  width: 400px;
  height: 400px;
  bottom: -50px;
  left: -50px;
  animation: float 14s ease-in-out infinite reverse;
}

.bg-decoration-3 {
  width: 300px;
  height: 300px;
  top: 40%;
  left: 40%;
  animation: pulse 8s ease-in-out infinite;
}

@keyframes float {
  0% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(30px, 20px);
  }
  100% {
    transform: translate(0, 0);
  }
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 0.1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.2;
  }
  100% {
    transform: scale(1);
    opacity: 0.1;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: $sm) {
  .login-card {
    width: 90%;
    max-width: 360px;
    padding: 30px;
  }
  
  .logo {
    width: 60px;
    height: 60px;
  }
  
  .title {
    font-size: 20px;
  }
}
</style> 