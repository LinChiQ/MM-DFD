<template>
  <div class="detection-create-container">
    <div class="page-title">新闻检测</div>
    
    <el-row :gutter="20">
      <el-col :span="16">
        <el-card shadow="hover" class="detection-card">
          <div slot="header" class="clearfix">
            <span>输入新闻信息</span>
            <el-button 
              style="float: right; padding: 3px 0;" 
              type="text" 
              @click="resetForm"
            >
              清空表单
            </el-button>
          </div>
          
          <el-form 
            ref="detectionForm" 
            :model="detectionForm" 
            :rules="rules" 
            label-position="top"
          >
            <el-form-item label="新闻标题" prop="title">
              <el-input v-model="detectionForm.title" placeholder="输入新闻标题"></el-input>
            </el-form-item>
            
            <el-form-item label="新闻内容" prop="content">
              <el-input 
                type="textarea" 
                v-model="detectionForm.content" 
                placeholder="输入新闻内容" 
                :rows="8"
              ></el-input>
            </el-form-item>
            
            <el-form-item label="新闻图片" prop="image">
              <el-upload
                class="upload-demo"
                drag
                action="#"
                :auto-upload="false"
                :on-change="handleImageChange"
                :limit="1"
                :file-list="fileList"
              >
                <i class="el-icon-upload"></i>
                <div class="el-upload__text">拖拽图片到此处，或<em>点击上传</em></div>
                <div class="el-upload__tip" slot="tip">只能上传jpg/png/jpeg文件，且不超过10MB</div>
              </el-upload>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="submitForm" :loading="loading">开始检测</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card shadow="hover" class="info-card">
          <div slot="header" class="clearfix">
            <span>检测说明</span>
          </div>
          <div class="info-content">
            <p>本系统支持多模态虚假新闻检测，结合文本内容与图像分析，提供更准确的检测结果。</p>
            <h4>使用须知：</h4>
            <ul>
              <li>新闻标题和内容均为必填项</li>
              <li>图片可选（提供图片将启用多模态检测）</li>
              <li>支持JPG、JPEG、PNG格式图片</li>
              <li>检测历史可在"检测历史"页面查看</li>
            </ul>
            <h4>检测流程：</h4>
            <ol>
              <li>输入新闻内容</li>
              <li>上传相关图片（可选）</li>
              <li>点击"开始检测"按钮</li>
              <li>系统分析并返回结果</li>
            </ol>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'DetectionCreate',
  data() {
    return {
      detectionForm: {
        title: '',
        content: '',
        image: null
      },
      rules: {
        title: [
          { required: true, message: '请输入新闻标题', trigger: 'blur' },
          { min: 2, max: 100, message: '标题长度在2到100个字符之间', trigger: 'blur' }
        ],
        content: [
          { required: true, message: '请输入新闻内容', trigger: 'blur' },
          { min: 10, message: '内容不能少于10个字符', trigger: 'blur' }
        ]
      },
      fileList: [],
      loading: false
    }
  },
  methods: {
    handleImageChange(file) {
      // 上传前校验文件类型和大小
      const isImage = file.raw.type.includes('image/')
      const isLt10M = file.raw.size / 1024 / 1024 < 10
      
      if (!isImage) {
        this.$message.error('上传文件只能是图片格式!')
        this.fileList = []
        return false
      }
      
      if (!isLt10M) {
        this.$message.error('上传图片大小不能超过 10MB!')
        this.fileList = []
        return false
      }
      
      // 设置当前图片
      this.detectionForm.image = file.raw
      this.fileList = [file]
    },
    
    submitForm() {
      this.$refs.detectionForm.validate(valid => {
        if (valid) {
          this.loading = true
          
          const formData = new FormData();
          formData.append('title', this.detectionForm.title);
          formData.append('content', this.detectionForm.content);
          
          if (this.detectionForm.image) {
            formData.append('image', this.detectionForm.image);
          }
          
          axios.post('/detection/detections/', formData, {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          })
            .then(response => {
              this.$message.success('检测任务已提交')
              // 修正：跳转到包含父路径的完整路由
              this.$router.push(`/dashboard/detection/detail/${response.data.id}`)
            })
            .catch(error => {
              console.error('检测提交失败:', error)
              this.$message.error('检测提交失败: ' + (error.response?.data?.detail || '请稍后重试'))
            })
            .finally(() => {
              this.loading = false
            })
        } else {
          return false
        }
      })
    },
    
    resetForm() {
      this.$refs.detectionForm.resetFields()
      this.fileList = []
      this.detectionForm.image = null
    }
  }
}
</script>

<style scoped>
.detection-create-container {
  padding: 20px;
}

.detection-card {
  margin-bottom: 20px;
}

.info-card {
  margin-bottom: 20px;
}

.info-content {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}

.info-content h4 {
  margin-top: 16px;
  margin-bottom: 8px;
  color: #303133;
}

.info-content ul, .info-content ol {
  padding-left: 20px;
  margin-bottom: 16px;
}

.info-content li {
  margin-bottom: 5px;
}
</style> 