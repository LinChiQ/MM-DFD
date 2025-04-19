<template>
  <div class="admin-users">
    <div class="page-header">
      <h1 class="page-title">用户管理</h1>
      <el-button type="primary" icon="el-icon-plus" @click="handleCreate">添加用户</el-button>
    </div>
    
    <!-- 搜索过滤 -->
    <el-card shadow="hover" class="filter-container">
      <el-form :inline="true" :model="filterForm" class="demo-form-inline">
        <el-form-item label="用户名">
          <el-input v-model="filterForm.username" placeholder="用户名" clearable></el-input>
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="filterForm.email" placeholder="邮箱" clearable></el-input>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterForm.active" placeholder="状态" clearable>
            <el-option label="激活" :value="true"></el-option>
            <el-option label="禁用" :value="false"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilter">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 用户列表 -->
    <el-card shadow="hover" class="user-list">
      <div slot="header" class="clearfix">
        <span>用户列表</span>
        <el-button style="float: right;" icon="el-icon-refresh" circle @click="fetchUsers"></el-button>
      </div>
      
      <el-table
        :data="tableData"
        style="width: 100%"
        border
        v-loading="loading"
        fit
      >
        <el-table-column
          prop="username"
          label="用户名"
          min-width="120">
        </el-table-column>
        <el-table-column
          prop="email"
          label="邮箱"
          min-width="200">
        </el-table-column>
        <el-table-column
          prop="date_joined"
          label="注册时间"
          min-width="180"
          sortable>
          <template slot-scope="scope">
            {{ formatDateTime(scope.row.date_joined) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="total_detections"
          label="检测次数"
          min-width="100">
        </el-table-column>
        <el-table-column
          prop="is_active"
          label="状态"
          min-width="100">
          <template slot-scope="scope">
            <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
              {{ scope.row.is_active ? '激活' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="is_staff"
          label="管理员"
          min-width="100">
          <template slot-scope="scope">
            <el-tag v-if="scope.row.is_staff" type="warning">是</el-tag>
            <el-tag v-else type="info">否</el-tag>
          </template>
        </el-table-column>
        <el-table-column
          fixed="right"
          label="操作"
          min-width="220">
          <template slot-scope="scope">
            <el-button
              size="mini"
              @click="handleEdit(scope.row)">编辑</el-button>
            <el-button
              v-if="scope.row.is_active"
              size="mini"
              type="danger"
              @click="handleDeactivate(scope.row)">禁用</el-button>
            <el-button
              v-else
              size="mini"
              type="success"
              @click="handleActivate(scope.row)">激活</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          background
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="currentPage"
          :page-sizes="[10, 20, 30, 50]"
          :page-size="pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total">
        </el-pagination>
      </div>
    </el-card>
    
    <!-- 用户编辑/创建对话框 -->
    <el-dialog
      :title="dialogType === 'create' ? '添加用户' : '编辑用户'"
      :visible.sync="dialogVisible"
      width="500px">
      <el-form :model="userForm" :rules="rules" ref="userForm" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" :disabled="dialogType === 'edit'"></el-input>
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email"></el-input>
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="dialogType === 'create'">
          <el-input v-model="userForm.password" type="password" show-password></el-input>
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword" v-if="dialogType === 'create'">
          <el-input v-model="userForm.confirmPassword" type="password" show-password></el-input>
        </el-form-item>
        <el-form-item label="名" prop="first_name">
          <el-input v-model="userForm.first_name"></el-input>
        </el-form-item>
        <el-form-item label="姓" prop="last_name">
          <el-input v-model="userForm.last_name"></el-input>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch
            v-model="userForm.is_active"
            active-text="激活"
            inactive-text="禁用">
          </el-switch>
        </el-form-item>
        <el-form-item label="管理员权限">
          <el-switch
            v-model="userForm.is_staff"
            active-text="启用"
            inactive-text="禁用">
          </el-switch>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">确定</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'AdminUsers',
  data() {
    // 自定义验证规则
    const validatePassword = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请输入密码'));
      } else if (value.length < 6) {
        callback(new Error('密码不能少于6个字符'));
      } else {
        if (this.userForm.confirmPassword !== '') {
          this.$refs.userForm.validateField('confirmPassword');
        }
        callback();
      }
    };
    const validateConfirmPassword = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请再次输入密码'));
      } else if (value !== this.userForm.password) {
        callback(new Error('两次输入密码不一致!'));
      } else {
        callback();
      }
    };
    
    return {
      loading: false,
      submitting: false,
      filterForm: {
        username: '',
        email: '',
        active: ''
      },
      tableData: [],
      currentPage: 1,
      pageSize: 10,
      total: 0,
      dialogVisible: false,
      dialogType: 'create', // create or edit
      userForm: {
        id: null,
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
        first_name: '',
        last_name: '',
        is_active: true,
        is_staff: false
      },
      rules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 3, max: 50, message: '长度在 3 到 50 个字符', trigger: 'blur' }
        ],
        email: [
          { required: true, message: '请输入邮箱地址', trigger: 'blur' },
          { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
        ],
        password: [
          { required: true, validator: validatePassword, trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, validator: validateConfirmPassword, trigger: 'blur' }
        ],
        first_name: [
          { required: true, message: '请输入名', trigger: 'blur' }
        ],
        last_name: [
          { required: true, message: '请输入姓', trigger: 'blur' }
        ]
      }
    }
  },
  created() {
    this.fetchUsers();
  },
  methods: {
    // 格式化日期时间
    formatDateTime(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleString();
    },
    
    // 获取用户列表
    fetchUsers() {
      this.loading = true;
      
      // 构建查询参数
      const params = {
        page: this.currentPage,
        page_size: this.pageSize
      };
      
      if (this.filterForm.username) {
        params.username = this.filterForm.username;
      }
      
      if (this.filterForm.email) {
        params.email = this.filterForm.email;
      }
      
      if (this.filterForm.active !== '') {
        params.is_active = this.filterForm.active;
      }
      
      axios.get('/users/', { params })
        .then(response => {
          this.tableData = response.data.results;
          this.total = response.data.count;
          this.loading = false;
        })
        .catch(error => {
          console.error('获取用户列表失败:', error);
          this.$message.error('获取用户列表失败');
          this.loading = false;
        });
    },
    
    // 处理筛选
    handleFilter() {
      this.currentPage = 1;
      this.fetchUsers();
    },
    
    // 重置筛选
    resetFilter() {
      this.filterForm = {
        username: '',
        email: '',
        active: ''
      };
      this.currentPage = 1;
      this.fetchUsers();
    },
    
    // 处理页码变化
    handleCurrentChange(val) {
      this.currentPage = val;
      this.fetchUsers();
    },
    
    // 处理每页条数变化
    handleSizeChange(val) {
      this.pageSize = val;
      this.currentPage = 1;
      this.fetchUsers();
    },
    
    // 打开创建用户对话框
    handleCreate() {
      this.dialogType = 'create';
      this.userForm = {
        id: null,
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
        first_name: '',
        last_name: '',
        is_active: true,
        is_staff: false
      };
      this.dialogVisible = true;
      this.$nextTick(() => {
        this.$refs.userForm.clearValidate();
      });
    },
    
    // 打开编辑用户对话框
    handleEdit(row) {
      this.dialogType = 'edit';
      this.userForm = {
        id: row.id,
        username: row.username,
        email: row.email,
        password: '',
        confirmPassword: '',
        first_name: row.first_name || '',
        last_name: row.last_name || '',
        is_active: row.is_active,
        is_staff: row.is_staff
      };
      this.dialogVisible = true;
      this.$nextTick(() => {
        this.$refs.userForm.clearValidate();
      });
    },
    
    // 禁用用户
    handleDeactivate(row) {
      this.$confirm('确定要禁用该用户吗?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        axios.patch(`/users/${row.id}/`, { is_active: false })
          .then(() => {
            this.$message.success('用户已禁用');
            this.fetchUsers();
          })
          .catch(error => {
            console.error('禁用用户失败:', error);
            this.$message.error('禁用用户失败');
          });
      }).catch(() => {});
    },
    
    // 激活用户
    handleActivate(row) {
      axios.patch(`/users/${row.id}/`, { is_active: true })
        .then(() => {
          this.$message.success('用户已激活');
          this.fetchUsers();
        })
        .catch(error => {
          console.error('激活用户失败:', error);
          this.$message.error('激活用户失败');
        });
    },
    
    // 提交表单
    submitForm() {
      this.$refs.userForm.validate(valid => {
        if (valid) {
          this.submitting = true;
          
          const formData = {
            username: this.userForm.username,
            email: this.userForm.email,
            first_name: this.userForm.first_name,
            last_name: this.userForm.last_name,
            is_active: this.userForm.is_active,
            is_staff: this.userForm.is_staff
          };
          
          if (this.dialogType === 'create') {
            formData.password = this.userForm.password;
            
            axios.post('/users/', formData)
              .then(() => {
                this.$message.success('用户创建成功');
                this.dialogVisible = false;
                this.fetchUsers();
                this.submitting = false;
              })
              .catch(error => {
                console.error('创建用户失败:', error);
                this.$message.error('创建用户失败: ' + (error.response?.data?.detail || '未知错误'));
                this.submitting = false;
              });
          } else {
            axios.patch(`/users/${this.userForm.id}/`, formData)
              .then(() => {
                this.$message.success('用户更新成功');
                this.dialogVisible = false;
                this.fetchUsers();
                this.submitting = false;
              })
              .catch(error => {
                console.error('更新用户失败:', error);
                this.$message.error('更新用户失败: ' + (error.response?.data?.detail || '未知错误'));
                this.submitting = false;
              });
          }
        }
      });
    }
  }
}
</script>

<style scoped>
.admin-users {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  margin: 0;
}

.filter-container {
  margin-bottom: 20px;
  padding: 15px;
}

.user-list {
  margin-bottom: 20px;
  width: 100%;
}

.pagination-container {
  margin-top: 20px;
  text-align: right;
}

/* 添加表格样式 */
/deep/ .el-table {
  width: 100%;
}

/deep/ .el-table__body {
  width: 100%;
}

/deep/ .el-table .cell {
  padding-left: 10px;
  padding-right: 10px;
}
</style> 