<template>
  <div class="dashboard-container">
    <div class="page-title">仪表盘</div>
    
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover" class="dashboard-card">
          <div class="card-content">
            <div class="card-icon">
              <i class="el-icon-s-data"></i>
            </div>
            <div class="card-info">
              <div class="card-title">检测总数</div>
              <div class="card-value">{{ stats.total_count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="dashboard-card">
          <div class="card-content">
            <div class="card-icon real">
              <i class="el-icon-check"></i>
            </div>
            <div class="card-info">
              <div class="card-title">真实新闻</div>
              <div class="card-value">{{ stats.real_count }} ({{ stats.real_percentage }}%)</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="dashboard-card">
          <div class="card-content">
            <div class="card-icon fake">
              <i class="el-icon-close"></i>
            </div>
            <div class="card-info">
              <div class="card-title">虚假新闻</div>
              <div class="card-value">{{ stats.fake_count }} ({{ stats.fake_percentage }}%)</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="dashboard-card">
          <div class="card-content">
            <div class="card-icon pending">
              <i class="el-icon-loading"></i>
            </div>
            <div class="card-info">
              <div class="card-title">待处理</div>
              <div class="card-value">{{ stats.pending_count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card shadow="hover" class="chart-card">
          <div slot="header" class="clearfix">
            <span>检测结果分布</span>
          </div>
          <div class="chart-container" ref="pieChart"></div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card shadow="hover" class="chart-card">
          <div slot="header" class="clearfix">
            <span>近期检测统计</span>
          </div>
          <div class="chart-container" ref="lineChart"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card shadow="hover">
          <div slot="header" class="clearfix">
            <span>最近检测</span>
            <el-button style="float: right; padding: 3px 0" type="text" @click="viewMore">查看更多</el-button>
          </div>
          
          <el-table
            :data="recentDetections"
            style="width: 100%"
            v-loading="loading"
            border
          >
            <el-table-column
              prop="title"
              label="标题"
              width="300"
            ></el-table-column>
            <el-table-column
              prop="created_at"
              label="检测时间"
              width="180"
            >
              <template slot-scope="scope">
                {{ formatDate(scope.row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column
              prop="status"
              label="状态"
              width="100"
            >
              <template slot-scope="scope">
                <el-tag :type="getStatusType(scope.row.status)">{{ getStatusText(scope.row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column
              prop="result"
              label="结果"
              width="100"
            >
              <template slot-scope="scope">
                <el-tag v-if="scope.row.result != null" :type="scope.row.result ? 'success' : 'danger'">
                  {{ scope.row.result ? '真实' : '虚假' }}
                </el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column
              prop="confidence"
              label="置信度"
              width="100"
            >
              <template slot-scope="scope">
                <div v-if="scope.row.confidence != null">{{ (scope.row.confidence * 100).toFixed(2) }}%</div>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column
              fixed="right"
              label="操作"
              width="120"
            >
              <template slot-scope="scope">
                <el-button
                  @click="viewDetail(scope.row.id)"
                  type="text"
                  size="small">
                  查看详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'DashboardView',
  data() {
    return {
      loading: false,
      recentDetections: []
    }
  },
  computed: {
    ...mapGetters(['detectionStats']),
    stats() {
      return this.detectionStats || {
        total_count: 0,
        fake_count: 0,
        real_count: 0,
        pending_count: 0,
        completed_count: 0,
        failed_count: 0,
        fake_percentage: 0,
        real_percentage: 0,
        average_confidence: 0
      }
    }
  },
  mounted() {
    this.fetchData()
  },
  methods: {
    fetchData() {
      this.loading = true
      
      // 获取统计数据
      this.$store.dispatch('detection/getDetectionStats')
        .catch(error => {
          console.error('获取统计数据失败:', error)
          this.$message.error('获取统计数据失败，请稍后重试')
        })
      
      // 获取最近的检测记录
      this.$store.dispatch('detection/getDetectionHistory')
        .then(detections => {
          this.recentDetections = detections.slice(0, 5) // 只显示前5条
        })
        .catch(error => {
          console.error('获取检测历史失败:', error)
          this.$message.error('获取检测历史失败，请稍后重试')
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
    
    viewDetail(id) {
      this.$router.push(`/detection/detail/${id}`)
    },
    
    viewMore() {
      this.$router.push('/detection/history')
    }
  }
}
</script>

<style lang="scss" scoped>
@import "@/assets/css/variables.scss";

.dashboard-container {
  padding: 20px;
}

.dashboard-card {
  height: 120px;
  
  .card-content {
    display: flex;
    align-items: center;
    height: 100%;
  }
  
  .card-icon {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background-color: $primary-color;
    display: flex;
    justify-content: center;
    align-items: center;
    margin-right: 20px;
    
    i {
      font-size: 30px;
      color: white;
    }
    
    &.real {
      background-color: $success-color;
    }
    
    &.fake {
      background-color: $danger-color;
    }
    
    &.pending {
      background-color: $warning-color;
    }
  }
  
  .card-info {
    display: flex;
    flex-direction: column;
    
    .card-title {
      font-size: 14px;
      color: $regular-font-color;
      margin-bottom: 10px;
    }
    
    .card-value {
      font-size: 24px;
      font-weight: bold;
      color: $main-font-color;
    }
  }
}

.chart-row {
  margin-top: 20px;
  margin-bottom: 20px;
}

.chart-card {
  height: 400px;
  
  .chart-container {
    height: 100%;
  }
}
</style> 