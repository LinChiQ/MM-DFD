<template>
  <div class="admin-settings">
    <div class="page-header">
      <h1 class="page-title">系统参数设置</h1>
      <div class="page-actions">
        <el-button type="primary" icon="el-icon-refresh" @click="loadSettings">刷新</el-button>
      </div>
    </div>
    
    <el-card shadow="hover" class="setting-card">
      <div slot="header" class="clearfix">
        <span>模型权重配置</span>
        <el-tooltip content="模型权重用于融合本地模型和LLM模型的预测结果" placement="top">
          <i class="el-icon-question"></i>
        </el-tooltip>
      </div>
      
      <div v-loading="loading">
        <el-form :model="weightForm" ref="weightForm" label-width="150px" :rules="rules">
          <el-form-item label="本地模型权重" prop="localModelWeight">
            <el-slider
              v-model="weightForm.localModelWeight"
              :format-tooltip="formatTooltip"
              :min="0"
              :max="1"
              :step="0.05"
              show-stops
            ></el-slider>
            <span class="weight-value">{{ formatTooltip(weightForm.localModelWeight) }}</span>
          </el-form-item>
          
          <el-form-item label="LLM模型权重" prop="llmWeight">
            <el-slider
              v-model="weightForm.llmWeight"
              :format-tooltip="formatTooltip"
              :min="0"
              :max="1"
              :step="0.05"
              show-stops
              :disabled="true"
            ></el-slider>
            <span class="weight-value">{{ formatTooltip(weightForm.llmWeight) }}</span>
          </el-form-item>
          
          <el-divider content-position="center">模型融合阈值设置</el-divider>
          
          <el-form-item label="虚假新闻阈值" prop="fakeThreshold">
            <el-slider
              v-model="weightForm.fakeThreshold"
              :format-tooltip="formatTooltip"
              :min="0.5"
              :max="0.9"
              :step="0.05"
              show-stops
            ></el-slider>
            <el-tooltip content="得分高于此阈值的新闻将被判定为虚假新闻" placement="top">
              <i class="el-icon-question"></i>
            </el-tooltip>
            <span class="weight-value">{{ formatTooltip(weightForm.fakeThreshold) }}</span>
          </el-form-item>
          
          <el-form-item label="真实新闻阈值" prop="realThreshold">
            <el-slider
              v-model="weightForm.realThreshold"
              :format-tooltip="formatTooltip"
              :min="0.1"
              :max="0.5"
              :step="0.05"
              show-stops
            ></el-slider>
            <el-tooltip content="得分低于此阈值的新闻将被判定为真实新闻" placement="top">
              <i class="el-icon-question"></i>
            </el-tooltip>
            <span class="weight-value">{{ formatTooltip(weightForm.realThreshold) }}</span>
          </el-form-item>
          
          <el-form-item>
            <el-button type="primary" @click="saveSettings" :loading="saving">保存设置</el-button>
            <el-button @click="resetForm">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>
    
    <el-card shadow="hover" class="setting-card">
      <div slot="header" class="clearfix">
        <span>API配置</span>
      </div>
      
      <div v-loading="loading">
        <el-form :model="apiForm" ref="apiForm" label-width="150px" :rules="apiRules">
          <el-form-item label="OpenRouter API密钥" prop="openrouterApiKey">
            <el-input 
              v-model="apiForm.openrouterApiKey" 
              placeholder="sk-or-v1-..." 
              show-password
              clearable
            ></el-input>
            <div class="form-help-text">
              <i class="el-icon-info"></i>
              用于LLM交叉验证的OpenRouter API密钥
            </div>
          </el-form-item>
          
          <el-form-item label="GPU加速" prop="useGpu">
            <el-switch
              v-model="apiForm.useGpu"
              active-text="启用"
              inactive-text="禁用"
            ></el-switch>
            <div class="form-help-text">
              <i class="el-icon-info"></i>
              启用GPU加速可以提高检测速度，但需要服务器支持CUDA
            </div>
          </el-form-item>
          
          <el-form-item>
            <el-button type="primary" @click="saveApiSettings" :loading="saving">保存API设置</el-button>
            <el-button @click="resetApiForm">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'AdminSettings',
  data() {
    return {
      loading: false,
      saving: false,
      
      // 模型权重表单
      weightForm: {
        localModelWeight: 0.4,
        llmWeight: 0.6,
        fakeThreshold: 0.65,
        realThreshold: 0.35
      },
      
      // API设置表单
      apiForm: {
        openrouterApiKey: '',
        useGpu: false
      },
      
      // 表单验证规则
      rules: {
        localModelWeight: [
          { required: true, message: '请设置本地模型权重', trigger: 'change' }
        ],
        fakeThreshold: [
          { required: true, message: '请设置虚假新闻阈值', trigger: 'change' }
        ],
        realThreshold: [
          { required: true, message: '请设置真实新闻阈值', trigger: 'change' }
        ]
      },
      
      // API设置表单验证规则
      apiRules: {
        openrouterApiKey: [
          { pattern: /^sk-or-v1-[a-zA-Z0-9]+$/, message: '无效的API密钥格式', trigger: 'blur' }
        ]
      }
    }
  },
  watch: {
    'weightForm.localModelWeight': function(val) {
      this.weightForm.llmWeight = parseFloat((1 - val).toFixed(2))
    }
  },
  created() {
    this.loadSettings()
  },
  methods: {
    // 格式化滑块提示
    formatTooltip(val) {
      return parseFloat(val).toFixed(2)
    },
    
    // 加载设置
    loadSettings() {
      this.loading = true
      
      // 由于后端没有实现list方法，我们需要使用model_weights action来获取数据
      axios.get('/settings/model_weights/')
        .then(response => {
          const data = response.data
          this.weightForm = {
            localModelWeight: data.local_model_weight,
            llmWeight: data.llm_weight,
            fakeThreshold: data.fake_threshold,
            realThreshold: data.real_threshold
          }
          
          this.apiForm = {
            openrouterApiKey: data.openrouter_api_key || '',
            useGpu: data.use_gpu || false
          }
          
          this.loading = false
        })
        .catch(error => {
          console.error('加载设置失败:', error)
          this.$message.error('加载设置失败，请重试')
          this.loading = false
        })
    },
    
    // 保存模型权重设置
    saveSettings() {
      this.$refs.weightForm.validate(valid => {
        if (valid) {
          this.saving = true
          
          // 使用model_weights action的POST方法保存设置
          axios.post('/settings/model_weights/', {
            local_model_weight: this.weightForm.localModelWeight,
            llm_weight: this.weightForm.llmWeight,
            fake_threshold: this.weightForm.fakeThreshold,
            real_threshold: this.weightForm.realThreshold
          })
            .then(() => {
              this.$message.success('模型权重设置已保存')
              this.saving = false
            })
            .catch(error => {
              console.error('保存设置失败:', error)
              this.$message.error('保存设置失败，请重试')
              this.saving = false
            })
        }
      })
    },
    
    // 保存API设置
    saveApiSettings() {
      this.$refs.apiForm.validate(valid => {
        if (valid) {
          this.saving = true
          
          // 使用api_config action的POST方法保存API设置
          axios.post('/settings/api_config/', {
            openrouter_api_key: this.apiForm.openrouterApiKey,
            use_gpu: this.apiForm.useGpu
          })
            .then(() => {
              this.$message.success('API设置已保存')
              this.saving = false
            })
            .catch(error => {
              console.error('保存API设置失败:', error)
              this.$message.error('保存API设置失败，请重试')
              this.saving = false
            })
        }
      })
    },
    
    // 重置表单
    resetForm() {
      this.$refs.weightForm.resetFields()
      this.loadSettings()
    },
    
    // 重置API表单
    resetApiForm() {
      this.$refs.apiForm.resetFields()
      this.loadSettings()
    }
  }
}
</script>

<style scoped>
.admin-settings {
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

.setting-card {
  margin-bottom: 20px;
}

.weight-value {
  margin-left: 10px;
  color: #409EFF;
  font-weight: bold;
}

.form-help-text {
  color: #909399;
  font-size: 12px;
  margin-top: 5px;
}
</style> 