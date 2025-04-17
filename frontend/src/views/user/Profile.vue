<template>
  <div class="profile-container">
    <div class="page-title">个人中心</div>
    
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card shadow="hover" class="user-card">
          <div class="user-avatar">
            <el-avatar :size="100" icon="el-icon-user-solid"></el-avatar>
          </div>
          <div class="user-info">
            <h3>{{ userInfo.username }}</h3>
            <p>{{ userInfo.email }}</p>
            <p>{{ userInfo.is_staff ? '管理员' : '普通用户' }}</p>
            <p>注册时间: {{ formatDate(userInfo.date_joined) }}</p>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="16">
        <el-card shadow="hover" class="info-edit-card">
          <div slot="header" class="clearfix">
            <span>个人资料</span>
          </div>
          
          <el-form :model="userForm" :rules="rules" ref="userForm" label-width="100px">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="userForm.username"></el-input>
            </el-form-item>
            
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="userForm.email"></el-input>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="updateUserInfo" :loading="updateLoading">保存修改</el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <el-card shadow="hover" class="password-card">
          <div slot="header" class="clearfix">
            <span>修改密码</span>
          </div>
          
          <el-form :model="passwordForm" :rules="passwordRules" ref="passwordForm" label-width="100px">
            <el-form-item label="当前密码" prop="old_password">
              <el-input v-model="passwordForm.old_password" type="password"></el-input>
            </el-form-item>
            
            <el-form-item label="新密码" prop="new_password">
              <el-input v-model="passwordForm.new_password" type="password"></el-input>
            </el-form-item>
            
            <el-form-item label="确认密码" prop="confirm_password">
              <el-input v-model="passwordForm.confirm_password" type="password"></el-input>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="changePassword" :loading="passwordLoading">修改密码</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'ProfileView',
  data() {
    // 密码确认验证
    const validatePass = (rule, value, callback) => {
      if (value !== this.passwordForm.new_password) {
        callback(new Error('两次输入密码不一致!'))
      } else {
        callback()
      }
    }
    
    return {
      userForm: {
        username: '',
        email: ''
      },
      passwordForm: {
        old_password: '',
        new_password: '',
        confirm_password: ''
      },
      rules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
        ],
        email: [
          { required: true, message: '请输入邮箱地址', trigger: 'blur' },
          { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
        ]
      },
      passwordRules: {
        old_password: [
          { required: true, message: '请输入当前密码', trigger: 'blur' }
        ],
        new_password: [
          { required: true, message: '请输入新密码', trigger: 'blur' },
          { min: 6, message: '密码长度不能小于6个字符', trigger: 'blur' }
        ],
        confirm_password: [
          { required: true, message: '请再次输入密码', trigger: 'blur' },
          { validator: validatePass, trigger: 'blur' }
        ]
      },
      updateLoading: false,
      passwordLoading: false
    }
  },
  computed: {
    ...mapGetters(['user']),
    userInfo() {
      return this.user || {}
    }
  },
  mounted() {
    this.initUserForm()
  },
  methods: {
    initUserForm() {
      this.userForm = {
        username: this.userInfo.username || '',
        email: this.userInfo.email || ''
      }
    },
    
    formatDate(dateString) {
      if (!dateString) return '-'
      const date = new Date(dateString)
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    },
    
    updateUserInfo() {
      this.$refs.userForm.validate(valid => {
        if (valid) {
          this.updateLoading = true
          this.$store.dispatch('user/updateUserInfo', this.userForm)
            .then(() => {
              this.$message.success('个人资料已更新')
            })
            .catch(error => {
              console.error('更新资料失败:', error)
              this.$message.error('更新资料失败: ' + (error.response?.data?.detail || '请稍后重试'))
            })
            .finally(() => {
              this.updateLoading = false
            })
        } else {
          return false
        }
      })
    },
    
    changePassword() {
      this.$refs.passwordForm.validate(valid => {
        if (valid) {
          this.passwordLoading = true
          this.$store.dispatch('user/changePassword', this.passwordForm)
            .then(() => {
              this.$message.success('密码已修改，请重新登录')
              // 清空表单
              this.passwordForm = {
                old_password: '',
                new_password: '',
                confirm_password: ''
              }
              // 登出并跳转到登录页
              this.$store.dispatch('user/logout')
            })
            .catch(error => {
              console.error('修改密码失败:', error)
              this.$message.error('修改密码失败: ' + (error.response?.data?.detail || '当前密码可能不正确'))
            })
            .finally(() => {
              this.passwordLoading = false
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
@import "@/assets/css/variables.scss";

.profile-container {
  padding: 20px;
}

.user-card {
  text-align: center;
  padding: 20px;
  margin-bottom: 20px;
  
  .user-avatar {
    margin-bottom: 20px;
  }
  
  .user-info {
    h3 {
      margin-top: 0;
      margin-bottom: 10px;
      color: $main-font-color;
    }
    
    p {
      margin: 5px 0;
      color: $regular-font-color;
    }
  }
}

.info-edit-card {
  margin-bottom: 20px;
}

.password-card {
  margin-bottom: 20px;
}
</style> 