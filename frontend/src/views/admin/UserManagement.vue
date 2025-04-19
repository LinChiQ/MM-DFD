<template>
  <div class="user-management">
    <div class="page-header">
      <h1 class="page-title">用户管理</h1>
      <el-button type="primary" @click="showAddUserDialog">添加用户</el-button>
    </div>
    
    <!-- 搜索和筛选 -->
    <el-card shadow="hover" class="filter-container">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="用户名">
          <el-input v-model="searchForm.username" placeholder="请输入用户名" clearable></el-input>
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="searchForm.email" placeholder="请输入邮箱" clearable></el-input>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="请选择状态" clearable>
            <el-option label="启用" value="active"></el-option>
            <el-option label="禁用" value="inactive"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="searchForm.role" placeholder="请选择角色" clearable>
            <el-option label="普通用户" value="user"></el-option>
            <el-option label="管理员" value="admin"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="handleSearch">搜索</el-button>
          <el-button icon="el-icon-refresh" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 用户列表 -->
    <el-card shadow="hover" class="list-container">
      <div slot="header" class="clearfix">
        <span>用户列表</span>
        <el-button style="float: right; padding: 3px 0" type="text" @click="refreshUserList">刷新列表</el-button>
      </div>
      
      <el-table
        :data="userList"
        border
        style="width: 100%"
        v-loading="loading"
        @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55"></el-table-column>
        <el-table-column type="index" width="50" label="序号"></el-table-column>
        <el-table-column prop="avatar" label="头像" width="80">
          <template slot-scope="scope">
            <el-avatar :size="40" :src="scope.row.avatar">
              {{ scope.row.username.charAt(0).toUpperCase() }}
            </el-avatar>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" width="120"></el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="200"></el-table-column>
        <el-table-column prop="role" label="角色" width="100">
          <template slot-scope="scope">
            <el-tag :type="scope.row.role === 'admin' ? 'danger' : 'primary'">
              {{ scope.row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template slot-scope="scope">
            <el-tag :type="scope.row.status === 'active' ? 'success' : 'info'">
              {{ scope.row.status === 'active' ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="detection_count" label="检测次数" width="100"></el-table-column>
        <el-table-column prop="register_time" label="注册时间" width="180"></el-table-column>
        <el-table-column prop="last_login" label="最后登录" width="180"></el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template slot-scope="scope">
            <el-button
              size="mini"
              type="primary"
              plain
              @click="handleEdit(scope.row)"
              icon="el-icon-edit"
              circle></el-button>
            <el-button
              size="mini"
              type="warning"
              plain
              @click="handleResetPassword(scope.row)"
              icon="el-icon-key"
              circle></el-button>
            <el-button
              size="mini"
              :type="scope.row.status === 'active' ? 'info' : 'success'"
              plain
              @click="handleToggleStatus(scope.row)"
              :icon="scope.row.status === 'active' ? 'el-icon-lock' : 'el-icon-unlock'"
              circle></el-button>
            <el-button
              size="mini"
              type="danger"
              plain
              @click="handleDelete(scope.row)"
              icon="el-icon-delete"
              circle></el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 批量操作 -->
      <div class="batch-operation">
        <el-button
          :disabled="selectedUsers.length === 0"
          size="small"
          @click="batchEnable">批量启用</el-button>
        <el-button
          :disabled="selectedUsers.length === 0"
          size="small"
          @click="batchDisable">批量禁用</el-button>
        <el-button
          :disabled="selectedUsers.length === 0"
          size="small"
          type="danger"
          @click="batchDelete">批量删除</el-button>
      </div>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="pagination.currentPage"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pagination.pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total">
        </el-pagination>
      </div>
    </el-card>
    
    <!-- 添加/编辑用户对话框 -->
    <el-dialog
      :title="dialogType === 'add' ? '添加用户' : '编辑用户'"
      :visible.sync="userFormVisible"
      width="500px">
      <el-form :model="userForm" :rules="userFormRules" ref="userForm" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" :disabled="dialogType === 'edit'"></el-input>
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email"></el-input>
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="dialogType === 'add'">
          <el-input v-model="userForm.password" type="password" show-password></el-input>
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword" v-if="dialogType === 'add'">
          <el-input v-model="userForm.confirmPassword" type="password" show-password></el-input>
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="userForm.role" placeholder="请选择角色">
            <el-option label="普通用户" value="user"></el-option>
            <el-option label="管理员" value="admin"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="userForm.status">
            <el-radio label="active">启用</el-radio>
            <el-radio label="inactive">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="userFormVisible = false">取 消</el-button>
        <el-button type="primary" @click="submitUserForm" :loading="formSubmitting">确 定</el-button>
      </div>
    </el-dialog>
    
    <!-- 重置密码对话框 -->
    <el-dialog
      title="重置密码"
      :visible.sync="resetPasswordVisible"
      width="400px">
      <el-form :model="resetPasswordForm" :rules="resetPasswordRules" ref="resetPasswordForm" label-width="100px">
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="resetPasswordForm.newPassword" type="password" show-password></el-input>
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="resetPasswordForm.confirmPassword" type="password" show-password></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="resetPasswordVisible = false">取 消</el-button>
        <el-button type="primary" @click="submitResetPassword" :loading="resetPasswordSubmitting">确 定</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
export default {
  name: 'UserManagement',
  data() {
    // 校验邮箱
    const validateEmail = (rule, value, callback) => {
      const emailRegex = /^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$/;
      if (!value) {
        callback(new Error('请输入邮箱地址'));
      } else if (!emailRegex.test(value)) {
        callback(new Error('请输入正确的邮箱地址'));
      } else {
        callback();
      }
    };
    
    // 校验确认密码
    const validateConfirmPassword = (rule, value, callback) => {
      if (value !== this.userForm.password) {
        callback(new Error('两次输入密码不一致'));
      } else {
        callback();
      }
    };
    
    // 校验重置密码
    const validateResetConfirmPassword = (rule, value, callback) => {
      if (value !== this.resetPasswordForm.newPassword) {
        callback(new Error('两次输入密码不一致'));
      } else {
        callback();
      }
    };
    
    return {
      // 搜索表单
      searchForm: {
        username: '',
        email: '',
        status: '',
        role: ''
      },
      
      // 用户列表
      userList: [],
      loading: true,
      selectedUsers: [],
      
      // 分页配置
      pagination: {
        currentPage: 1,
        pageSize: 10,
        total: 0
      },
      
      // 用户表单
      userFormVisible: false,
      dialogType: 'add', // 'add' 或 'edit'
      formSubmitting: false,
      userForm: {
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
        role: 'user',
        status: 'active'
      },
      userFormRules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
        ],
        email: [
          { required: true, message: '请输入邮箱地址', trigger: 'blur' },
          { validator: validateEmail, trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, message: '密码长度不能少于6个字符', trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, message: '请再次输入密码', trigger: 'blur' },
          { validator: validateConfirmPassword, trigger: 'blur' }
        ],
        role: [
          { required: true, message: '请选择角色', trigger: 'change' }
        ],
        status: [
          { required: true, message: '请选择状态', trigger: 'change' }
        ]
      },
      
      // 重置密码
      resetPasswordVisible: false,
      resetPasswordSubmitting: false,
      currentUser: null,
      resetPasswordForm: {
        newPassword: '',
        confirmPassword: ''
      },
      resetPasswordRules: {
        newPassword: [
          { required: true, message: '请输入新密码', trigger: 'blur' },
          { min: 6, message: '密码长度不能少于6个字符', trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, message: '请再次输入密码', trigger: 'blur' },
          { validator: validateResetConfirmPassword, trigger: 'blur' }
        ]
      }
    };
  },
  created() {
    this.getUserList();
  },
  methods: {
    // 获取用户列表
    getUserList() {
      this.loading = true;
      
      // 这里应该是实际的API调用
      // this.$http.get('/api/users', {
      //   params: {
      //     page: this.pagination.currentPage,
      //     limit: this.pagination.pageSize,
      //     ...this.searchForm
      //   }
      // }).then(response => {
      //   this.userList = response.data.users;
      //   this.pagination.total = response.data.total;
      //   this.loading = false;
      // }).catch(error => {
      //   console.error('获取用户列表失败:', error);
      //   this.loading = false;
      //   this.$message.error('获取用户列表失败');
      // });
      
      // 模拟数据
      setTimeout(() => {
        const mockUsers = [];
        const total = 126;
        const startIndex = (this.pagination.currentPage - 1) * this.pagination.pageSize + 1;
        const endIndex = Math.min(startIndex + this.pagination.pageSize - 1, total);
        
        for (let i = startIndex; i <= endIndex; i++) {
          const isAdmin = i === 1; // 第一个用户是管理员
          mockUsers.push({
            id: i,
            username: i === 1 ? 'admin' : `user${i}`,
            email: i === 1 ? 'admin@example.com' : `user${i}@example.com`,
            role: isAdmin ? 'admin' : 'user',
            status: Math.random() > 0.2 ? 'active' : 'inactive',
            avatar: '',
            detection_count: Math.floor(Math.random() * 100),
            register_time: '2023-' + Math.floor(Math.random() * 12 + 1).toString().padStart(2, '0') + '-' +
                          Math.floor(Math.random() * 28 + 1).toString().padStart(2, '0') + ' ' +
                          Math.floor(Math.random() * 24).toString().padStart(2, '0') + ':' +
                          Math.floor(Math.random() * 60).toString().padStart(2, '0') + ':' +
                          Math.floor(Math.random() * 60).toString().padStart(2, '0'),
            last_login: '2023-' + Math.floor(Math.random() * 12 + 1).toString().padStart(2, '0') + '-' +
                        Math.floor(Math.random() * 28 + 1).toString().padStart(2, '0') + ' ' +
                        Math.floor(Math.random() * 24).toString().padStart(2, '0') + ':' +
                        Math.floor(Math.random() * 60).toString().padStart(2, '0') + ':' +
                        Math.floor(Math.random() * 60).toString().padStart(2, '0')
          });
        }
        
        // 根据搜索条件筛选
        if (this.searchForm.username) {
          mockUsers = mockUsers.filter(user => user.username.includes(this.searchForm.username));
        }
        if (this.searchForm.email) {
          mockUsers = mockUsers.filter(user => user.email.includes(this.searchForm.email));
        }
        if (this.searchForm.status) {
          mockUsers = mockUsers.filter(user => user.status === this.searchForm.status);
        }
        if (this.searchForm.role) {
          mockUsers = mockUsers.filter(user => user.role === this.searchForm.role);
        }
        
        this.userList = mockUsers;
        this.pagination.total = total;
        this.loading = false;
      }, 500);
    },
    
    // 搜索
    handleSearch() {
      this.pagination.currentPage = 1;
      this.getUserList();
    },
    
    // 重置搜索
    resetSearch() {
      this.searchForm = {
        username: '',
        email: '',
        status: '',
        role: ''
      };
      this.handleSearch();
    },
    
    // 刷新用户列表
    refreshUserList() {
      this.getUserList();
    },
    
    // 处理页码变化
    handleCurrentChange(page) {
      this.pagination.currentPage = page;
      this.getUserList();
    },
    
    // 处理每页显示数量变化
    handleSizeChange(size) {
      this.pagination.pageSize = size;
      this.pagination.currentPage = 1;
      this.getUserList();
    },
    
    // 多选变化
    handleSelectionChange(selection) {
      this.selectedUsers = selection;
    },
    
    // 显示添加用户对话框
    showAddUserDialog() {
      this.dialogType = 'add';
      this.userForm = {
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
        role: 'user',
        status: 'active'
      };
      this.userFormVisible = true;
      this.$nextTick(() => {
        this.$refs.userForm && this.$refs.userForm.clearValidate();
      });
    },
    
    // 编辑用户
    handleEdit(row) {
      this.dialogType = 'edit';
      this.userForm = {
        id: row.id,
        username: row.username,
        email: row.email,
        role: row.role,
        status: row.status
      };
      this.userFormVisible = true;
      this.$nextTick(() => {
        this.$refs.userForm && this.$refs.userForm.clearValidate();
      });
    },
    
    // 提交用户表单
    submitUserForm() {
      this.$refs.userForm.validate(valid => {
        if (valid) {
          this.formSubmitting = true;
          
          // 这里应该是实际的API调用
          // const apiMethod = this.dialogType === 'add' ? 'post' : 'put';
          // const apiUrl = this.dialogType === 'add' ? '/api/users' : `/api/users/${this.userForm.id}`;
          // this.$http[apiMethod](apiUrl, this.userForm)
          //   .then(response => {
          //     this.formSubmitting = false;
          //     this.userFormVisible = false;
          //     this.$message.success(this.dialogType === 'add' ? '添加用户成功' : '编辑用户成功');
          //     this.getUserList();
          //   })
          //   .catch(error => {
          //     console.error(this.dialogType === 'add' ? '添加用户失败:' : '编辑用户失败:', error);
          //     this.formSubmitting = false;
          //     this.$message.error(this.dialogType === 'add' ? '添加用户失败' : '编辑用户失败');
          //   });
          
          // 模拟API调用
          setTimeout(() => {
            this.formSubmitting = false;
            this.userFormVisible = false;
            this.$message.success(this.dialogType === 'add' ? '添加用户成功' : '编辑用户成功');
            this.getUserList();
          }, 1000);
        }
      });
    },
    
    // 重置密码
    handleResetPassword(row) {
      this.currentUser = row;
      this.resetPasswordForm = {
        newPassword: '',
        confirmPassword: ''
      };
      this.resetPasswordVisible = true;
      this.$nextTick(() => {
        this.$refs.resetPasswordForm && this.$refs.resetPasswordForm.clearValidate();
      });
    },
    
    // 提交重置密码
    submitResetPassword() {
      this.$refs.resetPasswordForm.validate(valid => {
        if (valid) {
          this.resetPasswordSubmitting = true;
          
          // 这里应该是实际的API调用
          // this.$http.post(`/api/users/${this.currentUser.id}/reset-password`, {
          //   newPassword: this.resetPasswordForm.newPassword
          // })
          //   .then(response => {
          //     this.resetPasswordSubmitting = false;
          //     this.resetPasswordVisible = false;
          //     this.$message.success('密码重置成功');
          //   })
          //   .catch(error => {
          //     console.error('密码重置失败:', error);
          //     this.resetPasswordSubmitting = false;
          //     this.$message.error('密码重置失败');
          //   });
          
          // 模拟API调用
          setTimeout(() => {
            this.resetPasswordSubmitting = false;
            this.resetPasswordVisible = false;
            this.$message.success('密码重置成功');
          }, 1000);
        }
      });
    },
    
    // 切换用户状态
    handleToggleStatus(row) {
      const action = row.status === 'active' ? '禁用' : '启用';
      
      this.$confirm(`确定要${action}用户 "${row.username}" 吗?`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        // 这里应该是实际的API调用
        // this.$http.put(`/api/users/${row.id}/toggle-status`, {
        //   status: row.status === 'active' ? 'inactive' : 'active'
        // })
        //   .then(response => {
        //     this.$message.success(`${action}用户成功`);
        //     // 更新本地数据
        //     row.status = row.status === 'active' ? 'inactive' : 'active';
        //   })
        //   .catch(error => {
        //     console.error(`${action}用户失败:`, error);
        //     this.$message.error(`${action}用户失败`);
        //   });
        
        // 模拟API调用
        setTimeout(() => {
          this.$message.success(`${action}用户成功`);
          // 更新本地数据
          row.status = row.status === 'active' ? 'inactive' : 'active';
        }, 300);
      }).catch(() => {
        // 取消操作
      });
    },
    
    // 删除用户
    handleDelete(row) {
      this.$confirm(`确定要删除用户 "${row.username}" 吗?`, '警告', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error'
      }).then(() => {
        // 这里应该是实际的API调用
        // this.$http.delete(`/api/users/${row.id}`)
        //   .then(response => {
        //     this.$message.success('删除用户成功');
        //     this.getUserList();
        //   })
        //   .catch(error => {
        //     console.error('删除用户失败:', error);
        //     this.$message.error('删除用户失败');
        //   });
        
        // 模拟API调用
        setTimeout(() => {
          this.$message.success('删除用户成功');
          this.getUserList();
        }, 300);
      }).catch(() => {
        // 取消操作
      });
    },
    
    // 批量启用
    batchEnable() {
      if (this.selectedUsers.length === 0) return;
      
      const usernames = this.selectedUsers.map(user => user.username).join('、');
      this.$confirm(`确定要启用选中的 ${this.selectedUsers.length} 个用户吗?`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        // 实际API调用
        // const userIds = this.selectedUsers.map(user => user.id);
        // this.$http.post('/api/users/batch-enable', { userIds })
        //   .then(response => {
        //     this.$message.success('批量启用成功');
        //     this.getUserList();
        //   })
        //   .catch(error => {
        //     console.error('批量启用失败:', error);
        //     this.$message.error('批量启用失败');
        //   });
        
        // 模拟API调用
        setTimeout(() => {
          this.$message.success('批量启用成功');
          this.getUserList();
        }, 300);
      }).catch(() => {
        // 取消操作
      });
    },
    
    // 批量禁用
    batchDisable() {
      if (this.selectedUsers.length === 0) return;
      
      const usernames = this.selectedUsers.map(user => user.username).join('、');
      this.$confirm(`确定要禁用选中的 ${this.selectedUsers.length} 个用户吗?`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        // 实际API调用
        // const userIds = this.selectedUsers.map(user => user.id);
        // this.$http.post('/api/users/batch-disable', { userIds })
        //   .then(response => {
        //     this.$message.success('批量禁用成功');
        //     this.getUserList();
        //   })
        //   .catch(error => {
        //     console.error('批量禁用失败:', error);
        //     this.$message.error('批量禁用失败');
        //   });
        
        // 模拟API调用
        setTimeout(() => {
          this.$message.success('批量禁用成功');
          this.getUserList();
        }, 300);
      }).catch(() => {
        // 取消操作
      });
    },
    
    // 批量删除
    batchDelete() {
      if (this.selectedUsers.length === 0) return;
      
      this.$confirm(`确定要删除选中的 ${this.selectedUsers.length} 个用户吗?`, '警告', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error'
      }).then(() => {
        // 实际API调用
        // const userIds = this.selectedUsers.map(user => user.id);
        // this.$http.post('/api/users/batch-delete', { userIds })
        //   .then(response => {
        //     this.$message.success('批量删除成功');
        //     this.getUserList();
        //   })
        //   .catch(error => {
        //     console.error('批量删除失败:', error);
        //     this.$message.error('批量删除失败');
        //   });
        
        // 模拟API调用
        setTimeout(() => {
          this.$message.success('批量删除成功');
          this.getUserList();
        }, 300);
      }).catch(() => {
        // 取消操作
      });
    }
  }
};
</script>

<style lang="scss" scoped>
.user-management {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    .page-title {
      margin: 0;
      font-size: 24px;
      font-weight: bold;
    }
  }
  
  .filter-container {
    margin-bottom: 20px;
    
    .search-form {
      display: flex;
      flex-wrap: wrap;
    }
  }
  
  .list-container {
    margin-bottom: 20px;
  }
  
  .batch-operation {
    margin-top: 15px;
    margin-bottom: 15px;
  }
  
  .pagination-container {
    margin-top: 15px;
    display: flex;
    justify-content: flex-end;
  }
}
</style> 