<template>
  <div class="register-container">
    <div class="register-content">
      <div class="register-card">
        <div class="logo-container">
          <el-image :src="logoSrc" alt="Logo" class="logo"></el-image>
          <h2 class="title">用户注册</h2>
        </div>
        
        <el-form ref="registerForm" :model="registerForm" :rules="registerRules" class="register-form">
          <el-form-item prop="username">
            <el-input 
              v-model="registerForm.username" 
              prefix-icon="el-icon-user" 
              placeholder="用户名 (4-20个字符)"
              class="custom-input"
            />
          </el-form-item>
          
          <el-form-item prop="email">
            <el-input 
              v-model="registerForm.email" 
              prefix-icon="el-icon-message" 
              placeholder="邮箱"
              class="custom-input"
            />
          </el-form-item>
          
          <el-form-item prop="first_name">
            <el-input 
              v-model="registerForm.first_name" 
              prefix-icon="el-icon-user" 
              placeholder="名字"
              class="custom-input"
            />
          </el-form-item>
          
          <el-form-item prop="last_name">
            <el-input 
              v-model="registerForm.last_name" 
              prefix-icon="el-icon-user" 
              placeholder="姓氏"
              class="custom-input"
            />
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input 
              v-model="registerForm.password" 
              prefix-icon="el-icon-lock" 
              type="password" 
              placeholder="密码 (至少8位)"
              class="custom-input"
            />
          </el-form-item>
          
          <el-form-item prop="password2">
            <el-input 
              v-model="registerForm.password2" 
              prefix-icon="el-icon-lock" 
              type="password" 
              placeholder="确认密码"
              class="custom-input"
            />
          </el-form-item>
          
          <el-button 
            :loading="loading" 
            type="primary" 
            class="register-button" 
            @click="handleRegister"
          >
            注 册
          </el-button>
          
          <div class="register-options">
            <span>已有账号？</span>
            <span class="login-link" @click="goToLogin">立即登录</span>
          </div>
        </el-form>
      </div>
    </div>
    <div class="register-background">
      <div class="bg-decoration bg-decoration-1"></div>
      <div class="bg-decoration bg-decoration-2"></div>
      <div class="bg-decoration bg-decoration-3"></div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RegisterView',
  data() {
    const validatePass = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请输入密码'))
      } else if (value.length < 8) {
        callback(new Error('密码长度不能小于8个字符'))
      } else {
        if (this.registerForm.password2 !== '') {
          this.$refs.registerForm.validateField('password2')
        }
        callback()
      }
    }
    const validateConfirmPass = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请再次输入密码'))
      } else if (value !== this.registerForm.password) {
        callback(new Error('两次输入密码不一致!'))
      } else {
        callback()
      }
    }
    return {
      registerForm: {
        username: '',
        email: '',
        first_name: '',
        last_name: '',
        password: '',
        password2: ''
      },
      registerRules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
        ],
        email: [
          { required: true, message: '请输入邮箱地址', trigger: 'blur' },
          { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
        ],
        first_name: [
          { required: true, message: '请输入名字', trigger: 'blur' }
        ],
        last_name: [
          { required: true, message: '请输入姓氏', trigger: 'blur' }
        ],
        password: [
          { required: true, validator: validatePass, trigger: 'blur' }
        ],
        password2: [
          { required: true, validator: validateConfirmPass, trigger: 'blur' }
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
    handleRegister() {
      this.$refs.registerForm.validate(valid => {
        if (valid) {
          this.loading = true
          this.$store.dispatch('user/register', this.registerForm)
            .then(() => {
              this.$message.success('注册成功，请登录')
              this.$nextTick(() => {
                this.$router.push('/login')
              })
            })
            .catch(error => {
              console.error('注册失败:', error)
              if (error.response && error.response.data) {
                const errorData = error.response.data;
                if (errorData.password && Array.isArray(errorData.password)) {
                  this.$message.error('密码错误: ' + errorData.password.join(', '));
                } else if (errorData.detail) {
                  this.$message.error(errorData.detail);
                } else if (errorData.username) {
                  this.$message.error('用户名错误: ' + errorData.username.join(', '));
                } else if (errorData.email) {
                  this.$message.error('邮箱错误: ' + errorData.email.join(', '));
                } else {
                  this.$message.error('注册失败，请检查输入信息');
                }
              } else {
                this.$message.error('注册失败，请稍后重试');
              }
            })
            .finally(() => {
              this.loading = false
            })
        } else {
          return false
        }
      })
    },
    goToLogin() {
      this.$router.push('/login')
    }
  }
}
</script>

<style lang="scss" scoped>
@import "@/assets/css/variables.scss";

.register-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.register-content {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  position: relative;
  z-index: 2;
}

.register-card {
  width: 450px;
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

.register-form {
  margin-top: 20px;
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

.register-button {
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

.register-options {
  margin-top: 24px;
  display: flex;
  justify-content: center;
  gap: 5px;
}

.login-link {
  color: $primary-color;
  cursor: pointer;
  transition: color 0.3s;
  font-weight: 500;

  &:hover {
    color: darken($primary-color, 10%);
    text-decoration: underline;
  }
}

.register-background {
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
  .register-card {
    width: 90%;
    max-width: 400px;
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