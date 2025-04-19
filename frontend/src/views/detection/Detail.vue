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
                <div class="result-label">最终结论</div>
                <div class="result-value">
                  <el-tag :type="getResultType" size="medium">{{ getResultText }}</el-tag>
                </div>
              </div>
              
              <div class="result-item">
                <div class="result-label">最终置信度</div>
                <div class="result-value">
                  <el-progress 
                    :percentage="getConfidenceValue" 
                    :color="getResultType === 'danger' ? '#F56C6C' : '#67C23A'">
                  </el-progress>
                </div>
              </div>

              <el-collapse v-model="activeAnalysisSections" v-if="detection.analysis_result">
                <el-collapse-item title="详细分析过程" name="details">
                  <div class="analysis-section" v-if="analysisDetails.fusion">
                    <h4><i class="el-icon-connection"></i> 融合策略</h4>
                    <p>策略: {{ analysisDetails.fusion.strategy || '未知' }}</p>
                  </div>

                  <div class="analysis-section" v-if="analysisDetails.local_model">
                    <h4><i class="el-icon-cpu"></i> 本地模型分析</h4>
                    <p>结果: 
                      <el-tag 
                        :type="getVerdictType(analysisDetails.local_model.result)" 
                        size="small"
                      >
                        {{ getVerdictText(analysisDetails.local_model.result) }}
                      </el-tag>
                    </p>
                    <p>置信度: {{ (analysisDetails.local_model.confidence * 100).toFixed(2) }}%</p>
                    <p v-if="analysisDetails.local_model.error">错误: {{ analysisDetails.local_model.error }}</p>
                  </div>

                  <div class="analysis-section" v-if="analysisDetails.llm_verification">
                    <h4><i class="el-icon-chat-dot-round"></i> LLM 交叉验证</h4>
                    <p>综合判断: 
                       <el-tag 
                         :type="getLlmVerdictType(analysisDetails.llm_verification.overall_verdict)" 
                         size="small"
                       >
                         {{ analysisDetails.llm_verification.overall_verdict || '未知' }}
                       </el-tag>
                    </p>
                    <p>综合置信度: {{ (analysisDetails.llm_verification.aggregated_confidence * 100).toFixed(2) }}%</p>
                    <p v-if="analysisDetails.llm_verification.needs_manual_review" style="color: orange;"><i class="el-icon-warning-outline"></i> 需要人工审核</p>
                    <p v-if="analysisDetails.llm_verification.error">错误: {{ analysisDetails.llm_verification.error }}</p>
                    
                    <div v-if="llmIndividualResults.length > 0" style="margin-top: 10px;">
                       <el-button type="text" @click="llmDetailsDialogVisible = true">查看各模型详细结果</el-button>
                    </div>
                  </div>
                </el-collapse-item>
              </el-collapse>
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

    <el-dialog
      title="LLM 交叉验证详细结果"
      :visible.sync="llmDetailsDialogVisible"
      width="70%"
      top="5vh" 
    >
      <el-table :data="llmIndividualResults" size="medium" border stripe style="width: 100%">
        <el-table-column prop="model" label="模型" width="200" show-overflow-tooltip></el-table-column>
        <el-table-column prop="verdict" label="判断" width="110" align="center">
          <template slot-scope="scope">
            <el-tag :type="getLlmVerdictType(scope.row.verdict)" size="small">{{ scope.row.verdict }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="confidence" label="置信度" width="90" align="center">
           <template slot-scope="scope">
             {{ (scope.row.confidence * 100).toFixed(1) }}%
           </template>
        </el-table-column>
        <el-table-column prop="reason" label="理由" show-overflow-tooltip></el-table-column>
        <el-table-column prop="error" label="错误" width="120" show-overflow-tooltip></el-table-column>
      </el-table>
      <span slot="footer" class="dialog-footer">
        <el-button @click="llmDetailsDialogVisible = false">关 闭</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
export default {
  name: 'DetectionDetail',
  data() {
    return {
      loading: true,
      detectionId: null,
      pollingInterval: null,
      pollingDelay: 5000,
      activeAnalysisSections: ['details'],
      llmDetailsDialogVisible: false
    }
  },
  computed: {
    detection() {
      const det = this.$store.getters.currentDetection;
      if (det && (det.status === 'completed' || det.status === 'failed')) {
        this.stopPolling();
      }
      return det;
    },
    getResultType() {
      // 读取融合结果
      const verdict = this.analysisDetails.fusion?.final_verdict;
      if (!verdict) return 'info';
      return verdict === 'real' ? 'success' : (verdict === 'fake' ? 'danger' : 'info');
    },
    getResultText() {
      // 读取融合结果
      const verdict = this.analysisDetails.fusion?.final_verdict;
      if (!verdict) return '未知';
      return verdict === 'real' ? '真实新闻' : (verdict === 'fake' ? '虚假新闻' : '未知');
    },
    getConfidenceValue() {
      // 读取融合结果
      const confidence = this.analysisDetails.fusion?.final_confidence;
      if (confidence === null || confidence === undefined) return 0;
      return Math.round(confidence * 100);
    },
    isProcessing() {
      return this.detection && (this.detection.status === 'pending' || this.detection.status === 'processing');
    },
    analysisDetails() {
      if (this.detection && this.detection.analysis_result) {
        if (typeof this.detection.analysis_result === 'string') {
          try {
            return JSON.parse(this.detection.analysis_result);
          } catch (e) {
            console.error("Failed to parse analysis_result JSON:", e);
            return {};
          }
        } else {
          return this.detection.analysis_result;
        }
      } 
      return {};
    },
    llmIndividualResults() {
       if (this.analysisDetails && this.analysisDetails.llm_verification && this.analysisDetails.llm_verification.details) {
         const details = this.analysisDetails.llm_verification.details;
         const textResults = details.text_verifications || [];
         const imgResults = details.image_verifications || [];
         return [...textResults, ...imgResults];
       }
       return [];
    }
  },
  created() {
    this.detectionId = this.$route.params.id
    this.fetchDetailAndPoll();
  },
  beforeDestroy() {
    this.stopPolling();
  },
  methods: {
    fetchDetailAndPoll() {
      this.loading = true;
      this.$store.dispatch('detection/getDetectionDetail', this.detectionId)
        .then(() => {
          this.loading = false;
          if (this.isProcessing) {
            this.startPolling();
          }
        })
        .catch(error => {
          this.loading = false;
          console.error('获取检测详情失败:', error);
          this.$message.error('获取检测详情失败，请稍后重试');
        });
    },

    startPolling() {
      this.stopPolling();
      logger.info('开始轮询检测结果...');
      this.pollingInterval = setInterval(() => {
        if (!this.isProcessing) {
          this.stopPolling();
          return;
        }
        logger.debug(`轮询检测结果 ID: ${this.detectionId}`);
        this.$store.dispatch('detection/getDetectionDetail', this.detectionId)
          .catch(error => {
            console.error('轮询失败:', error);
          });
      }, this.pollingDelay);
    },

    stopPolling() {
      if (this.pollingInterval) {
        logger.info('停止轮询检测结果。');
        clearInterval(this.pollingInterval);
        this.pollingInterval = null;
      }
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
      this.fetchDetailAndPoll();
      this.$message.info('正在刷新结果...');
    },
    
    retryDetection() {
      this.stopPolling();
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
    },

    getVerdictType(result) {
      if (result === 'fake') return 'danger';
      if (result === 'real') return 'success';
      return 'info';
    },
    getVerdictText(result) {
      if (result === 'fake') return '虚假';
      if (result === 'real') return '真实';
      return '未知';
    },
    getLlmVerdictType(verdict) {
      if (!verdict) return 'info';
      const lowerVerdict = verdict.toLowerCase();
      if (lowerVerdict.includes('fake') || lowerVerdict.includes('虚假') || lowerVerdict.includes('伪造')) return 'danger';
      if (lowerVerdict.includes('true') || lowerVerdict.includes('真实')) return 'success';
      if (lowerVerdict.includes('uncertain') || lowerVerdict.includes('无法') || lowerVerdict.includes('混合')) return 'warning';
      return 'info';
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

.analysis-section {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;

  h4 {
    margin-bottom: 10px;
    font-size: 15px;
    color: #303133;
    i {
      margin-right: 5px;
    }
  }
  p {
    font-size: 14px;
    color: #606266;
    margin-bottom: 5px;
    line-height: 1.5;
  }
}
.analysis-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

::v-deep .el-collapse-item__header {
  font-size: 16px;
  font-weight: bold;
}
::v-deep .el-collapse-item__content {
  padding-top: 15px;
  padding-bottom: 10px;
}

::v-deep .result-card .el-card__body {
  padding-bottom: 5px;
}
</style> 