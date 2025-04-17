<template>
  <div class="login-container">
    <div class="login-form-container">
      <div class="login-header">
        <el-image :src="logoSrc" alt="Logo" class="logo"></el-image>
        <h2>多模态虚假新闻检测系统</h2>
      </div>
      <el-form :model="loginForm" :rules="loginRules" ref="loginForm" class="login-form">
        <el-form-item prop="username">
          <el-input 
            v-model="loginForm.username" 
            placeholder="用户名" 
            prefix-icon="el-icon-user">
          </el-input>
        </el-form-item>
        <el-form-item prop="password">
          <el-input 
            v-model="loginForm.password" 
            type="password" 
            placeholder="密码" 
            prefix-icon="el-icon-lock"
            @keyup.enter.native="handleLogin">
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button 
            type="primary" 
            :loading="loading" 
            @click="handleLogin" 
            class="login-button">
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Login',
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
          { required: true, message: '请输入密码', trigger: 'blur' }
        ]
      },
      loading: false
    }
  },
  computed: {
    logoSrc() {
      try {
        return require('@/assets/logo.png')
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
              this.$router.push({ path: this.redirect || '/' })
              this.loading = false
            })
            .catch(error => {
              this.$message.error(error.message || '登录失败')
              this.loading = false
            })
        } else {
          return false
        }
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: $background-color;
  background-size: cover;
}

.login-form-container {
  width: 400px;
  padding: 30px;
  background-color: white;
  border-radius: $border-radius;
  box-shadow: $box-shadow;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;

  h2 {
    margin-top: 15px;
    font-weight: 500;
    color: $primary-color;
  }

  .logo {
    width: 80px;
    height: 80px;
  }
}

.login-form {
  .login-button {
    width: 100%;
  }
}
</style> 