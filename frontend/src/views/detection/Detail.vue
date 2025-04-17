<template>
  <div class="detail-container">
    <div class="page-header">
      <el-page-header @back="goBack" :content="detection ? detection.title : '检测详情'"></el-page-header>
    </div>
    
    <div v-loading="loading">
      <el-row :gutter="20" v-if="detection">
        <el-col :span="16">
          <el-card class="detection-card">
            <div slot="header" class="clearfix">
              <span>新闻内容</span>
              <el-tag :type="getResultType" class="result-tag">{{ getResultText }}</el-tag>
            </div>
            
            <div class="detection-header">
              <h2>{{ detection.title }}</h2>
              <div class="detection-meta">
                <span>检测时间: {{ formatDate(detection.created_at) }}</span>
                <el-tag size="small" :type="getStatusType(detection.status)">{{ getStatusText(detection.status) }}</el-tag>
              </div>
            </div>
            
            <div class="detection-content">
              <div v-if="detection.image" class="detection-image">
                <el-image 
                  :src="detection.image" 
                  fit="cover"
                  :preview-src-list="[detection.image]">
                </el-image>
              </div>
              
              <div class="news-content">
                <p>{{ detection.content }}</p>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="8">
          <el-card class="result-card" v-if="detection.status === 'completed'">
            <div slot="header" class="clearfix">
              <span>检测结果</span>
            </div>
            
            <div class="result-info">
              <div class="result-item">
                <div class="result-label">结论</div>
                <div class="result-value">
                  <el-tag :type="getResultType" size="medium">{{ getResultText }}</el-tag>
                </div>
              </div>
              
              <div class="result-item">
                <div class="result-label">置信度</div>
                <div class="result-value">
                  <el-progress 
                    :percentage="getConfidenceValue" 
                    :color="getResultType === 'danger' ? '#F56C6C' : '#67C23A'">
                  </el-progress>
                </div>
              </div>
              
              <div class="result-item" v-if="detection.text_score !== undefined">
                <div class="result-label">文本分析</div>
                <div class="result-value">
                  <el-progress 
                    :percentage="detection.text_score * 100" 
                    :color="detection.text_score >= 0.5 ? '#67C23A' : '#F56C6C'">
                  </el-progress>
                </div>
              </div>
              
              <div class="result-item" v-if="detection.image_score !== undefined">
                <div class="result-label">图像分析</div>
                <div class="result-value">
                  <el-progress 
                    :percentage="detection.image_score * 100" 
                    :color="detection.image_score >= 0.5 ? '#67C23A' : '#F56C6C'">
                  </el-progress>
                </div>
              </div>
              
              <div class="result-item" v-if="detection.explanation">
                <div class="result-label">解释</div>
                <div class="result-value explanation">
                  {{ detection.explanation }}
                </div>
              </div>
            </div>
          </el-card>
          
          <el-card class="waiting-card" v-else-if="detection.status === 'pending' || detection.status === 'processing'">
            <div slot="header" class="clearfix">
              <span>检测中</span>
            </div>
            
            <div class="waiting-content">
              <i class="el-icon-loading"></i>
              <p>检测任务{{ detection.status === 'pending' ? '等待中' : '处理中' }}，请稍候...</p>
              <el-button type="primary" size="small" @click="refreshResult">刷新结果</el-button>
            </div>
          </el-card>
          
          <el-card class="error-card" v-else-if="detection.status === 'failed'">
            <div slot="header" class="clearfix">
              <span>检测失败</span>
            </div>
            
            <div class="error-content">
              <i class="el-icon-circle-close"></i>
              <p>很抱歉，检测任务处理失败。</p>
              <div v-if="detection.error_message" class="error-message">
                错误信息: {{ detection.error_message }}
              </div>
              <el-button type="primary" size="small" @click="retryDetection">重新检测</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <div v-else class="empty-state">
        <i class="el-icon-warning-outline"></i>
        <p>未找到检测数据或加载失败</p>
        <el-button type="primary" @click="goToHistory">返回历史记录</el-button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DetectionDetail',
  data() {
    return {
      loading: true,
      detectionId: null
    }
  },
  computed: {
    detection() {
      return this.$store.getters.currentDetection
    },
    getResultType() {
      if (!this.detection || this.detection.result === null) return ''
      return this.detection.result ? 'success' : 'danger'
    },
    getResultText() {
      if (!this.detection || this.detection.result === null) return '未知'
      return this.detection.result ? '真实新闻' : '虚假新闻'
    },
    getConfidenceValue() {
      if (!this.detection || this.detection.confidence === null) return 0
      return Math.round(this.detection.confidence * 100)
    }
  },
  created() {
    this.detectionId = this.$route.params.id
    this.fetchDetail()
  },
  methods: {
    fetchDetail() {
      this.loading = true
      this.$store.dispatch('detection/getDetectionDetail', this.detectionId)
        .catch(error => {
          console.error('获取检测详情失败:', error)
          this.$message.error('获取检测详情失败，请稍后重试')
        })
        .finally(() => {
          this.loading = false
        })
    },
    
    formatDate(dateString) {
      if (!dateString) return '-'
      const date = new Date(dateString)
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
    },
    
    getStatusType(status) {
      switch (status) {
        case 'completed': return 'success'
        case 'pending': return 'info'
        case 'processing': return 'warning'
        case 'failed': return 'danger'
        default: return 'info'
      }
    },
    
    getStatusText(status) {
      switch (status) {
        case 'completed': return '完成'
        case 'pending': return '等待中'
        case 'processing': return '处理中'
        case 'failed': return '失败'
        default: return '未知'
      }
    },
    
    goBack() {
      this.$router.go(-1)
    },
    
    goToHistory() {
      this.$router.push('/detection/history')
    },
    
    refreshResult() {
      this.$store.dispatch('detection/getDetectionResult', this.detectionId)
        .then(() => {
          if (this.detection.status === 'completed') {
            this.$message.success('检测已完成！')
          } else {
            this.$message.info('检测仍在进行中，请稍后再试')
          }
        })
        .catch(error => {
          console.error('刷新结果失败:', error)
          this.$message.error('刷新结果失败，请稍后重试')
        })
    },
    
    retryDetection() {
      // 重新提交检测
      const data = {
        title: this.detection.title,
        content: this.detection.content,
        image: this.detection.original_image
      }
      
      this.$store.dispatch('detection/createDetection', data)
        .then(response => {
          this.$message.success('已重新提交检测任务')
          this.$router.push(`/detection/detail/${response.id}`)
        })
        .catch(error => {
          console.error('重新检测失败:', error)
          this.$message.error('重新检测失败: ' + (error.response?.data?.detail || '请稍后重试'))
        })
    }
  }
}
</script>

<style lang="scss" scoped>
@import "@/assets/css/variables.scss";

.detail-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.detection-card {
  margin-bottom: 20px;
  
  .detection-header {
    margin-bottom: 20px;
    
    h2 {
      margin-top: 0;
      margin-bottom: 10px;
      color: $main-font-color;
    }
    
    .detection-meta {
      color: $secondary-font-color;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 14px;
    }
  }
  
  .detection-content {
    .detection-image {
      margin-bottom: 20px;
      
      .el-image {
        width: 100%;
        max-height: 400px;
        border-radius: 4px;
      }
    }
    
    .news-content {
      line-height: 1.6;
      color: $regular-font-color;
      white-space: pre-line;
    }
  }
}

.result-card, .waiting-card, .error-card {
  margin-bottom: 20px;
}

.result-info {
  .result-item {
    margin-bottom: 20px;
    
    .result-label {
      font-weight: bold;
      margin-bottom: 8px;
      color: $main-font-color;
    }
    
    .result-value {
      &.explanation {
        white-space: pre-line;
        line-height: 1.6;
        color: $regular-font-color;
      }
    }
  }
}

.waiting-content, .error-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 0;
  
  i {
    font-size: 48px;
    margin-bottom: 20px;
    color: $warning-color;
  }
  
  p {
    margin-bottom: 20px;
    color: $regular-font-color;
  }
  
  .error-message {
    margin-bottom: 20px;
    color: $danger-color;
    font-size: 14px;
  }
}

.error-content i {
  color: $danger-color;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 0;
  
  i {
    font-size: 60px;
    margin-bottom: 20px;
    color: $info-color;
  }
  
  p {
    margin-bottom: 20px;
    color: $regular-font-color;
  }
}

.result-tag {
  float: right;
  margin-top: 3px;
}
</style> 