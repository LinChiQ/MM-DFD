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
              <div class="card-value">{{ stats.real_count }} ({{ stats.real_percentage.toFixed(2) }}%)</div>
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
              <div class="card-value">{{ stats.fake_count }} ({{ stats.fake_percentage.toFixed(2) }}%)</div>
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
            fit
          >
            <el-table-column
              prop="title"
              label="标题"
              min-width="300"
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
              width="90"
            >
              <template slot-scope="scope">
                <el-tag v-if="scope.row.status === 'completed' && scope.row.result"
                        :type="getResultTagType(scope.row.result)">
                  {{ getResultText(scope.row.result) }}
                </el-tag>
                <span v-else-if="scope.row.status === 'completed'">未知</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column
              prop="confidence"
              label="置信度"
              width="100"
            >
              <template slot-scope="scope">
                <div v-if="scope.row.status === 'completed' && scope.row.confidence_score != null && scope.row.result !== 'unknown'">{{ (scope.row.confidence_score * 100).toFixed(2) }}%</div>
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
import * as echarts from 'echarts'

export default {
  name: 'DashboardView',
  data() {
    return {
      loading: false,
      recentDetections: [],
      pieChart: null,
      lineChart: null
    }
  },
  computed: {
    ...mapGetters(['detectionStats']),
    stats() {
      const statsData = this.detectionStats || {
        total_count: 0,
        fake_count: 0,
        real_count: 0,
        pending_count: 0,
        completed_count: 0,
        failed_count: 0,
        fake_percentage: 0,
        real_percentage: 0,
        average_confidence: 0
      };
      statsData.fake_percentage = Number(statsData.fake_percentage) || 0;
      statsData.real_percentage = Number(statsData.real_percentage) || 0;
      return statsData;
    }
  },
  watch: {
    stats(newStats) {
      if (newStats) {
        this.initPieChart();
      }
    },
    recentDetections(newDetections) {
      if (newDetections && newDetections.length > 0) {
         this.initLineChart();
      }
    }
  },
  mounted() {
    this.fetchData()
    window.addEventListener('resize', this.handleResize);
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.handleResize);
    if (this.pieChart) {
      this.pieChart.dispose();
      this.pieChart = null;
    }
    if (this.lineChart) {
      this.lineChart.dispose();
      this.lineChart = null;
    }
  },
  methods: {
    fetchData() {
      this.loading = true
      let statsLoaded = false;
      let historyLoaded = false;

      const checkAndInitCharts = () => {
        if (statsLoaded && historyLoaded) {
          this.$nextTick(() => {
             this.initPieChart();
             this.initLineChart();
          });
          this.loading = false;
        }
      };

      this.$store.dispatch('detection/getDetectionStats')
        .then(() => { statsLoaded = true; checkAndInitCharts(); })
        .catch(error => {
          console.error('获取统计数据失败:', error)
          this.$message.error('获取统计数据失败，请稍后重试')
          statsLoaded = true;
          checkAndInitCharts();
        });
      
      this.$store.dispatch('detection/getDetectionHistory')
        .then(detections => {
          this.recentDetections = detections.slice(0, 7);
          historyLoaded = true;
          checkAndInitCharts();
        })
        .catch(error => {
          console.error('获取检测历史失败:', error)
          this.$message.error('获取检测历史失败，请稍后重试')
          historyLoaded = true;
          checkAndInitCharts();
        });
    },
    
    initPieChart() {
      if (!this.$refs.pieChart) return;
      if (this.pieChart) {
        this.pieChart.dispose();
      }
      this.pieChart = echarts.init(this.$refs.pieChart);
      
      // 准备饼图数据
      const pieData = [];
      
      // 添加真实新闻数据
      if (this.stats.real_count > 0) {
        pieData.push({ 
          value: this.stats.real_count, 
          name: '真实新闻', 
          itemStyle: { color: '#67C23A' } 
        });
      }
      
      // 添加虚假新闻数据
      if (this.stats.fake_count > 0) {
        pieData.push({ 
          value: this.stats.fake_count, 
          name: '虚假新闻', 
          itemStyle: { color: '#F56C6C' } 
        });
      }
      
      // 添加其他类型的数据
      const otherCount = this.stats.completed_count - this.stats.real_count - this.stats.fake_count;
      if (otherCount > 0) {
        pieData.push({ 
          value: otherCount, 
          name: '其他类型', 
          itemStyle: { color: '#909399' } 
        });
      }
      
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 10,
          data: pieData.map(item => item.name)
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
                fontSize: '20',
                fontWeight: 'bold'
              }
            },
            labelLine: {
              show: false
            },
            data: pieData
          }
        ]
      };
      this.pieChart.setOption(option);
    },
    
    initLineChart() {
      if (!this.$refs.lineChart || !this.recentDetections || this.recentDetections.length === 0) return;
      if (this.lineChart) {
        this.lineChart.dispose();
      }
      this.lineChart = echarts.init(this.$refs.lineChart);
      
      const countsByDate = this.recentDetections.reduce((acc, detection) => {
        const date = this.formatDate(detection.created_at, true);
        acc[date] = (acc[date] || 0) + 1;
        return acc;
      }, {});
      
      const dates = Object.keys(countsByDate).sort();
      const counts = dates.map(date => countsByDate[date]);
      
      const option = {
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: dates
        },
        yAxis: {
          type: 'value',
           minInterval: 1
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        series: [
          {
            name: '检测数量',
            type: 'line',
            smooth: true,
            data: counts,
            itemStyle: { color: '#409EFF' },
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    {
                        offset: 0,
                        color: 'rgba(64, 158, 255, 0.3)'
                    },
                    {
                        offset: 1,
                        color: 'rgba(64, 158, 255, 0)'
                    }
                ])
            }
          }
        ]
      };
      this.lineChart.setOption(option);
    },
    
    handleResize() {
      if (this.pieChart) {
        this.pieChart.resize();
      }
      if (this.lineChart) {
        this.lineChart.resize();
      }
    },

    formatDate(dateString, dateOnly = false) {
      if (!dateString) return '-'
      const date = new Date(dateString)
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      if (dateOnly) {
          return `${year}-${month}-${day}`;
      }
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      return `${year}-${month}-${day} ${hours}:${minutes}`
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
      this.$router.push(`/dashboard/detection/detail/${id}`)
    },
    
    viewMore() {
      this.$router.push('/dashboard/detection/history')
    },

    getResultTagType(result) {
      if (result === 'fake') return 'danger';
      if (result === 'real') return 'success';
      if (result === 'uncertain') return 'warning';
      if (result === 'mixed') return 'warning';
      return 'info';
    },

    getResultText(result) {
      if (result === 'fake') return '虚假';
      if (result === 'real') return '真实';
      if (result === 'uncertain') return '不确定';
      if (result === 'mixed') return '混合';
      return result || '未知';
    },
  }
}
</script>

<style lang="scss" scoped>
@import "@/assets/css/variables.scss";

.dashboard-container {
  padding: 20px;
  height: calc(100vh - 84px);
  overflow-y: auto;
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
    height: 320px;
    width: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    color: #909399;
    font-size: 16px;
  }
}
</style> 