<template>
  <div class="detection-statistics">
    <div class="page-header">
      <h1 class="page-title">检测统计</h1>
      <div class="page-actions">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          @change="handleDateRangeChange"
          :picker-options="pickerOptions">
        </el-date-picker>
        <el-button type="primary" icon="el-icon-refresh" @click="loadStatistics">刷新数据</el-button>
      </div>
    </div>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="data-overview">
      <el-col :span="6">
        <el-card shadow="hover" class="data-card total-card">
          <div class="data-card-header">
            <div class="card-title">总检测量</div>
            <i class="el-icon-s-data icon"></i>
          </div>
          <div class="data-card-body">
            <div class="card-value">{{ statistics.total_count || 0 }}</div>
            <div class="card-trend">
              <span class="trend-text">完成率</span>
              <span class="trend-value">{{ calculateCompletionRate }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="data-card true-card">
          <div class="data-card-header">
            <div class="card-title">真新闻量</div>
            <i class="el-icon-circle-check icon"></i>
          </div>
          <div class="data-card-body">
            <div class="card-value">{{ statistics.real_count || 0 }}</div>
            <div class="card-trend">
              <span class="trend-text">占比</span>
              <span class="trend-value">{{ statistics.real_percentage ? statistics.real_percentage.toFixed(1) : '0.0' }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="data-card fake-card">
          <div class="data-card-header">
            <div class="card-title">假新闻量</div>
            <i class="el-icon-circle-close icon"></i>
          </div>
          <div class="data-card-body">
            <div class="card-value">{{ statistics.fake_count || 0 }}</div>
            <div class="card-trend">
              <span class="trend-text">占比</span>
              <span class="trend-value">{{ statistics.fake_percentage ? statistics.fake_percentage.toFixed(1) : '0.0' }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="data-card task-card">
          <div class="data-card-header">
            <div class="card-title">平均置信度</div>
            <i class="el-icon-view icon"></i>
          </div>
          <div class="data-card-body">
            <div class="card-value">{{ (statistics.average_confidence ? (statistics.average_confidence * 100).toFixed(1) : '0.0') }}%</div>
            <div class="card-trend">
              <span class="trend-text">基于</span>
              <span class="trend-value">{{ statistics.completed_count || 0 }}个完成任务</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card class="chart-card">
          <div slot="header" class="clearfix">
            <span>检测结果分布</span>
          </div>
          <div class="chart-container" v-loading="loading">
            <div ref="pieChart" style="width:100%; height:300px"></div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card">
          <div slot="header" class="clearfix">
            <span>检测状态分布</span>
          </div>
          <div class="chart-container" v-loading="loading">
            <div ref="statusChart" style="width:100%; height:300px"></div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 最近检测列表 -->
    <el-card class="recent-detection-card">
      <div slot="header" class="clearfix">
        <span>最近检测记录</span>
        <el-button style="float: right; padding: 3px 0" type="text" @click="viewAllDetections">查看全部</el-button>
      </div>
      <div v-loading="loadingDetections">
        <el-table :data="recentDetections" style="width: 100%" :row-class-name="getRowClassName">
          <el-table-column prop="id" label="ID" width="80"></el-table-column>
          <el-table-column prop="content" label="检测内容">
            <template slot-scope="scope">
              <div class="content-cell">
                <el-tooltip :content="scope.row.content" placement="top" :disabled="scope.row.content.length < 50">
                  <span>{{ truncateText(scope.row.content, 50) }}</span>
                </el-tooltip>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="user.username" label="用户" width="120"></el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template slot-scope="scope">
              <el-tag :type="getStatusType(scope.row.status)">
                {{ getStatusLabel(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="result" label="检测结果" width="100">
            <template slot-scope="scope">
              <el-tag v-if="scope.row.status === 'completed'" :type="scope.row.result ? 'success' : 'danger'">
                {{ scope.row.result ? '真实' : '虚假' }}
              </el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="confidence_score" label="置信度" width="120">
            <template slot-scope="scope">
              <el-progress 
                v-if="scope.row.status === 'completed'"
                :percentage="(scope.row.confidence_score * 100)" 
                :color="getConfidenceColor(scope.row.confidence_score)">
              </el-progress>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="检测时间" width="180"></el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script>
import * as echarts from 'echarts/core';
import { GridComponent, TooltipComponent, TitleComponent, LegendComponent } from 'echarts/components';
import { PieChart } from 'echarts/charts';
import { CanvasRenderer } from 'echarts/renderers';
import axios from 'axios';

echarts.use([GridComponent, TooltipComponent, TitleComponent, LegendComponent, PieChart, CanvasRenderer]);

export default {
  name: 'DetectionStatistics',
  data() {
    return {
      loading: false,
      loadingDetections: false,
      dateRange: [new Date(new Date().getTime() - 30 * 24 * 60 * 60 * 1000), new Date()],
      pickerOptions: {
        shortcuts: [{
          text: '最近一周',
          onClick(picker) {
            const end = new Date();
            const start = new Date();
            start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
            picker.$emit('pick', [start, end]);
          }
        }, {
          text: '最近一个月',
          onClick(picker) {
            const end = new Date();
            const start = new Date();
            start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);
            picker.$emit('pick', [start, end]);
          }
        }, {
          text: '最近三个月',
          onClick(picker) {
            const end = new Date();
            const start = new Date();
            start.setTime(start.getTime() - 3600 * 1000 * 24 * 90);
            picker.$emit('pick', [start, end]);
          }
        }]
      },
      // 统计数据
      statistics: {
        total_count: 0,
        fake_count: 0,
        real_count: 0,
        pending_count: 0,
        completed_count: 0,
        failed_count: 0,
        fake_percentage: 0,
        real_percentage: 0,
        average_confidence: 0
      },
      // 最近检测记录
      recentDetections: [],
      // 图表实例
      pieChart: null,
      statusChart: null
    }
  },
  computed: {
    calculateCompletionRate() {
      return this.statistics.total_count > 0
        ? ((this.statistics.completed_count / this.statistics.total_count) * 100).toFixed(1)
        : '0.0'
    }
  },
  created() {
    this.loadStatistics()
    this.loadRecentDetections()
  },
  mounted() {
    this.initCharts()
    // 监听窗口大小变化，调整图表大小
    window.addEventListener('resize', this.resizeCharts)
  },
  beforeDestroy() {
    // 移除事件监听
    window.removeEventListener('resize', this.resizeCharts)
    // 销毁图表实例
    if (this.pieChart) {
      this.pieChart.dispose()
    }
    if (this.statusChart) {
      this.statusChart.dispose()
    }
  },
  methods: {
    // 加载统计数据
    loadStatistics() {
      this.loading = true
      
      // 构建API参数
      const params = {}
      params.all = 'true' // 管理员查看所有数据
      
      if (this.dateRange && this.dateRange.length === 2) {
        params.start_date = this.formatDate(this.dateRange[0])
        params.end_date = this.formatDate(this.dateRange[1])
      }
      
      axios.get('/api/detection/get_stats/', { params })
        .then(response => {
          this.statistics = response.data
          this.updateCharts()
          this.loading = false
        })
        .catch(error => {
          console.error('获取统计数据失败:', error)
          this.$message.error('获取统计数据失败，请重试')
          this.loading = false
        })
    },
    
    // 加载最近检测记录
    loadRecentDetections() {
      this.loadingDetections = true
      
      axios.get('/api/detection/', {
        params: { page: 1, page_size: 10 } // 只获取最近10条
      })
        .then(response => {
          this.recentDetections = response.data.results || []
          this.loadingDetections = false
        })
        .catch(error => {
          console.error('获取检测记录失败:', error)
          this.$message.error('获取检测记录失败，请重试')
          this.loadingDetections = false
        })
    },
    
    // 初始化图表
    initCharts() {
      // 初始化饼图
      this.pieChart = echarts.init(this.$refs.pieChart)
      
      // 初始化状态图
      this.statusChart = echarts.init(this.$refs.statusChart)
      
      // 更新图表数据
      this.updateCharts()
    },
    
    // 更新图表数据
    updateCharts() {
      if (!this.pieChart || !this.statusChart) return
      
      // 更新检测结果饼图
      const pieOption = {
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          right: 10,
          top: 'center',
          data: ['真实新闻', '虚假新闻']
        },
        series: [
          {
            name: '检测结果',
            type: 'pie',
            radius: ['50%', '70%'],
            avoidLabelOverlap: false,
            label: {
              show: false,
              position: 'center'
            },
            emphasis: {
              label: {
                show: true,
                fontSize: '18',
                fontWeight: 'bold'
              }
            },
            labelLine: {
              show: false
            },
            data: [
              { value: this.statistics.real_count || 0, name: '真实新闻', itemStyle: { color: '#67C23A' } },
              { value: this.statistics.fake_count || 0, name: '虚假新闻', itemStyle: { color: '#F56C6C' } }
            ]
          }
        ]
      }
      
      // 更新检测状态饼图
      const statusOption = {
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          right: 10,
          top: 'center',
          data: ['已完成', '进行中', '失败']
        },
        series: [
          {
            name: '检测状态',
            type: 'pie',
            radius: ['50%', '70%'],
            avoidLabelOverlap: false,
            label: {
              show: false,
              position: 'center'
            },
            emphasis: {
              label: {
                show: true,
                fontSize: '18',
                fontWeight: 'bold'
              }
            },
            labelLine: {
              show: false
            },
            data: [
              { value: this.statistics.completed_count || 0, name: '已完成', itemStyle: { color: '#67C23A' } },
              { value: this.statistics.pending_count || 0, name: '进行中', itemStyle: { color: '#E6A23C' } },
              { value: this.statistics.failed_count || 0, name: '失败', itemStyle: { color: '#F56C6C' } }
            ]
          }
        ]
      }
      
      this.pieChart.setOption(pieOption)
      this.statusChart.setOption(statusOption)
    },
    
    // 调整图表大小
    resizeCharts() {
      if (this.pieChart) this.pieChart.resize()
      if (this.statusChart) this.statusChart.resize()
    },
    
    // 日期范围变化处理
    handleDateRangeChange() {
      this.loadStatistics()
    },
    
    // 查看所有检测
    viewAllDetections() {
      this.$router.push('/admin/detection/list')
    },
    
    // 获取行类名
    getRowClassName({ row }) {
      return row.status === 'failed' ? 'error-row' : ''
    },
    
    // 获取状态标签类型
    getStatusType(status) {
      switch (status) {
        case 'completed': return 'success'
        case 'pending': return 'warning'
        case 'failed': return 'danger'
        default: return 'info'
      }
    },
    
    // 获取状态标签文本
    getStatusLabel(status) {
      switch (status) {
        case 'completed': return '已完成'
        case 'pending': return '进行中'
        case 'failed': return '失败'
        default: return '未知'
      }
    },
    
    // 获取置信度颜色
    getConfidenceColor(confidence) {
      if (confidence >= 0.8) return '#67C23A'
      if (confidence >= 0.6) return '#E6A23C'
      return '#F56C6C'
    },
    
    // 日期格式化
    formatDate(date) {
      const d = new Date(date)
      const year = d.getFullYear()
      const month = ('0' + (d.getMonth() + 1)).slice(-2)
      const day = ('0' + d.getDate()).slice(-2)
      return `${year}-${month}-${day}`
    },
    
    // 文本截断
    truncateText(text, length) {
      if (!text) return ''
      return text.length > length ? text.substring(0, length) + '...' : text
    }
  }
}
</script>

<style scoped>
.detection-statistics {
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

.data-overview {
  margin-bottom: 20px;
}

.data-card {
  height: 120px;
  overflow: hidden;
}

.data-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.card-title {
  font-size: 16px;
  font-weight: 500;
}

.data-card-body {
  display: flex;
  flex-direction: column;
}

.card-value {
  font-size: 30px;
  font-weight: bold;
  margin-bottom: 5px;
}

.card-trend {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}

.total-card .icon {
  color: #409EFF;
  font-size: 24px;
}

.true-card .icon {
  color: #67C23A;
  font-size: 24px;
}

.fake-card .icon {
  color: #F56C6C;
  font-size: 24px;
}

.task-card .icon {
  color: #E6A23C;
  font-size: 24px;
}

.trend-value {
  font-weight: 500;
}

.trend-value.positive {
  color: #67C23A;
}

.trend-value.negative {
  color: #F56C6C;
}

.chart-row {
  margin-bottom: 20px;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  height: 300px;
}

.content-cell {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}

.error-row {
  background-color: #fef0f0;
}
</style> 