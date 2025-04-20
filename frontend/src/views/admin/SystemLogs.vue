<template>
  <div class="admin-logs">
    <div class="page-header">
      <h1 class="page-title">系统日志</h1>
      <div class="page-actions">
        <el-button type="primary" icon="el-icon-refresh" @click="loadLogs">刷新</el-button>
      </div>
    </div>
    
    <el-card shadow="hover">
      <div slot="header" class="clearfix">
        <span>系统日志查看</span>
      </div>
      
      <div class="description">
        <p>该页面显示系统运行日志文件的内容，帮助管理员排查系统运行问题。</p>
      </div>
      
      <div v-loading="loading">
        <el-table
          :data="logs"
          style="width: 100%"
          border
          stripe
          :max-height="600"
        >
          <el-table-column
            prop="timestamp"
            label="时间"
            width="240">
          </el-table-column>
          <el-table-column
            prop="level"
            label="级别"
            width="100">
            <template slot-scope="scope">
              <el-tag 
                :type="getLogLevelType(scope.row.level)"
                size="small">
                {{ scope.row.level }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="message"
            label="内容">
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'SystemLogs',
  data() {
    return {
      loading: false,
      logs: []
    }
  },
  created() {
    this.loadLogs()
  },
  methods: {
    // 加载日志
    loadLogs() {
      this.loading = true
      
      // 读取系统日志文件
      axios.get('/settings/logs/')
        .then(response => {
          this.logs = this.parseLogData(response.data)
          this.loading = false
        })
        .catch(error => {
          console.error('获取日志失败:', error)
          this.$message.error('获取日志失败，请重试')
          this.loading = false
          
          // 开发环境下使用模拟数据
          if (process.env.NODE_ENV === 'development') {
            this.loadMockData()
          }
        })
    },
    
    // 解析日志数据
    parseLogData(data) {
      if (!data || !data.logs || !Array.isArray(data.logs)) {
        return []
      }
      
      return data.logs.map((log, index) => ({
        id: index + 1,
        timestamp: log.timestamp || '',
        level: log.level || 'INFO',
        logger: log.logger || '',
        message: log.message || ''
      }))
    },
    
    // 加载模拟数据（开发阶段使用）
    loadMockData() {
      const mockLogs = []
      const levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG']
      const loggers = ['django.server', 'django.request', 'detection.views', 'users.views', 'settings.views']
      const messages = [
        '用户登录成功',
        '检测任务创建成功',
        '检测任务完成',
        '模型权重更新',
        '系统启动',
        '数据库连接错误',
        'API请求超时',
        '用户权限验证失败',
        '文件上传失败',
        '非法请求被拦截'
      ]
      
      // 生成50条模拟日志
      for (let i = 0; i < 50; i++) {
        const date = new Date()
        date.setMinutes(date.getMinutes() - i * 30)
        
        mockLogs.push({
          id: i + 1,
          timestamp: date.toISOString().replace('T', ' ').substring(0, 19),
          level: levels[Math.floor(Math.random() * levels.length)],
          logger: loggers[Math.floor(Math.random() * loggers.length)],
          message: messages[Math.floor(Math.random() * messages.length)]
        })
      }
      
      this.logs = mockLogs
    },
    
    // 获取日志级别标签类型
    getLogLevelType(level) {
      switch (level) {
        case 'ERROR': return 'danger'
        case 'WARNING': return 'warning'
        case 'INFO': return 'success'
        case 'DEBUG': return 'info'
        default: return ''
      }
    }
  }
}
</script>

<style scoped>
.admin-logs {
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

.description {
  margin-bottom: 20px;
  color: #606266;
}
</style> 