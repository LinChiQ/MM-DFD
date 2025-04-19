<template>
  <div class="admin-dashboard">
    <div class="page-header">
      <h1 class="page-title">管理员仪表盘</h1>
      <div class="page-actions">
        <el-button type="primary" icon="el-icon-refresh" @click="refreshData">刷新数据</el-button>
      </div>
    </div>
    
    <!-- 错误消息提示 -->
    <el-alert
      v-if="errorMessage"
      :title="errorMessage"
      type="error"
      :closable="true"
      show-icon
      style="margin-bottom: 20px;"
    >
    </el-alert>
    
    <!-- 数据概览卡片 -->
    <el-row :gutter="20" class="data-overview" v-loading="loading" element-loading-text="加载数据中...">
      <el-col :xs="12" :sm="12" :md="6" :lg="6" :xl="6">
        <el-card shadow="hover" class="data-card">
          <div slot="header" class="clearfix">
            <span>总用户数</span>
          </div>
          <div class="card-body">
            <div class="card-content">
              <div class="card-value">{{ statistics.totalUsers }}</div>
            </div>
            <div class="card-icon">
              <i class="el-icon-user"></i>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="12" :sm="12" :md="6" :lg="6" :xl="6">
        <el-card shadow="hover" class="data-card">
          <div slot="header" class="clearfix">
            <span>总检测量</span>
          </div>
          <div class="card-body">
            <div class="card-content">
              <div class="card-value">{{ statistics.totalDetections }}</div>
            </div>
            <div class="card-icon">
              <i class="el-icon-search"></i>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="12" :sm="12" :md="6" :lg="6" :xl="6">
        <el-card shadow="hover" class="data-card">
          <div slot="header" class="clearfix">
            <span>虚假新闻比例</span>
          </div>
          <div class="card-body">
            <div class="card-content">
              <div class="card-value">{{ statistics.fakeNewsRatio }}%</div>
            </div>
            <div class="card-icon">
              <i class="el-icon-warning"></i>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="12" :sm="12" :md="6" :lg="6" :xl="6">
        <el-card shadow="hover" class="data-card">
          <div slot="header" class="clearfix">
            <span>今日检测量</span>
          </div>
          <div class="card-body">
            <div class="card-content">
              <div class="card-value">{{ statistics.todayDetections }}</div>
            </div>
            <div class="card-icon">
              <i class="el-icon-date"></i>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 图表 -->
    <el-row :gutter="20" class="charts-row" v-loading="loading" element-loading-text="加载图表中...">
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card shadow="hover" class="chart-card">
          <div slot="header" class="clearfix">
            <span>检测统计</span>
          </div>
          <div class="chart-container" ref="weeklyTrendChart"></div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card shadow="hover" class="chart-card">
          <div slot="header" class="clearfix">
            <span>检测结果分布</span>
          </div>
          <div class="chart-container" ref="resultDistributionChart"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 最近检测列表 -->
    <el-card shadow="hover" class="recent-detections">
      <div slot="header" class="clearfix">
        <span>最近检测记录</span>
        <el-button style="float: right;" type="text" @click="viewAllDetections">查看全部</el-button>
      </div>
      
      <el-table
        :data="recentDetections"
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column
          prop="id"
          label="ID"
          width="80">
        </el-table-column>
        <el-table-column
          prop="user"
          label="用户"
          width="120">
        </el-table-column>
        <el-table-column
          prop="title"
          label="标题"
          show-overflow-tooltip>
        </el-table-column>
        <el-table-column
          prop="result"
          label="结果"
          width="100">
          <template slot-scope="scope">
            <el-tag :type="scope.row.result === '真实' ? 'success' : 'danger'">
              {{ scope.row.result }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="confidence"
          label="置信度"
          width="100">
          <template slot-scope="scope">
            {{ scope.row.confidence }}%
          </template>
        </el-table-column>
        <el-table-column
          prop="created_at"
          label="检测时间"
          width="180">
        </el-table-column>
        <el-table-column
          fixed="right"
          label="操作"
          width="100">
          <template slot-scope="scope">
            <el-button type="text" size="small" @click="viewDetail(scope.row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import * as echarts from 'echarts';
import axios from 'axios';

export default {
  name: 'AdminDashboard',
  data() {
    return {
      loading: false,
      statistics: {
        totalUsers: 0,
        totalDetections: 0,
        fakeNewsRatio: 0,
        todayDetections: 0
      },
      recentDetections: [],
      charts: {
        weeklyTrend: null,
        resultDistribution: null
      },
      errorMessage: ''
    }
  },
  created() {
    this.fetchData();
  },
  mounted() {
    this.initCharts();
  },
  methods: {
    // 获取数据
    fetchData() {
      this.loading = true;
      this.errorMessage = '';
      
      // 获取统计信息
      axios.get('/detection/detections/get_stats/?all=true')
        .then(response => {
          const data = response.data;
          
          this.statistics = {
            totalUsers: data.total_count || 0,
            totalDetections: data.total_count || 0,
            fakeNewsRatio: data.fake_percentage ? Math.round(data.fake_percentage) : 0,
            todayDetections: data.completed_count || 0
          };
          
          // 创建周趋势数据（因API未提供，创建模拟数据）
          if (!data.weekly_trend) {
            // 修改：只使用当前有的数据创建柱状图，不使用随机数据
            const todayData = {
              date: '今日检测量',
              count: this.statistics.todayDetections
            };
            this.updateWeeklyTrendChart([todayData]);
          } else {
            this.updateWeeklyTrendChart(data.weekly_trend);
          }
          
          // 创建结果分布数据
          if (!data.result_distribution) {
            const resultDistribution = [
              { name: '真实新闻', value: data.real_count || 0 },
              { name: '虚假新闻', value: data.fake_count || 0 }
            ];
            this.updateResultDistributionChart(resultDistribution);
          } else {
            this.updateResultDistributionChart(data.result_distribution);
          }
        })
        .catch(error => {
          console.error('获取统计数据失败:', error);
          this.errorMessage = '获取统计数据失败，请重试';
          this.$message.error('获取统计数据失败');
        })
        .finally(() => {
          this.loading = false;
        });
      
      // 获取最近的检测记录
      axios.get('/detection/detections/?limit=10')
        .then(response => {
          this.recentDetections = response.data.results.map(item => ({
            id: item.id,
            user: typeof item.user === 'string' ? item.user : (item.user?.username || '未知'),
            title: item.title,
            result: item.result === 'fake' ? '虚假' : (item.result === 'real' ? '真实' : '未知'),
            confidence: item.confidence_score ? Math.round(item.confidence_score * 100) : 0,
            created_at: new Date(item.created_at).toLocaleString()
          }));
        })
        .catch(error => {
          console.error('获取检测记录失败:', error);
          this.$message.error('获取检测记录失败');
        });
    },
    
    // 刷新数据
    refreshData() {
      this.fetchData();
    },
    
    // 初始化图表
    initCharts() {
      // 初始化周趋势图表
      this.charts.weeklyTrend = echarts.init(this.$refs.weeklyTrendChart);
      
      // 初始化结果分布图表
      this.charts.resultDistribution = echarts.init(this.$refs.resultDistributionChart);
      
      // 设置默认配置
      this.updateWeeklyTrendChart([]);
      this.updateResultDistributionChart([]);
      
      // 监听窗口大小变化，调整图表大小
      window.addEventListener('resize', this.resizeCharts);
    },
    
    // 更新周趋势图表
    updateWeeklyTrendChart(data) {
      // 修改：不再使用默认的7天数据
      if (!data || data.length === 0) {
        data = [
          { date: '今日检测量', count: 0 }
        ];
      }
      
      // 提取日期和数量
      const dates = data.map(item => item.date);
      const counts = data.map(item => item.count);
      
      // 设置图表配置
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: dates
        },
        yAxis: {
          type: 'value'
        },
        series: [{
          name: '检测数量',
          data: counts,
          type: 'bar', // 修改为柱状图
          itemStyle: {
            color: '#409EFF'
          }
        }]
      };
      
      this.charts.weeklyTrend.setOption(option);
    },
    
    // 更新结果分布图表
    updateResultDistributionChart(data) {
      // 如果没有数据，设置默认值
      if (!data || data.length === 0) {
        data = [
          { name: '真实新闻', value: 0 },
          { name: '虚假新闻', value: 0 }
        ];
      }
      
      // 设置图表配置
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 10,
          data: data.map(item => item.name)
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
                fontSize: '16',
                fontWeight: 'bold'
              }
            },
            labelLine: {
              show: false
            },
            data: [
              { value: data[0].value, name: '真实新闻', itemStyle: { color: '#67C23A' } },
              { value: data[1].value, name: '虚假新闻', itemStyle: { color: '#F56C6C' } }
            ]
          }
        ]
      };
      
      this.charts.resultDistribution.setOption(option);
    },
    
    // 调整图表大小
    resizeCharts() {
      this.charts.weeklyTrend.resize();
      this.charts.resultDistribution.resize();
    },
    
    // 查看所有检测
    viewAllDetections() {
      this.$router.push('/admin/detection/list');
    },
    
    // 查看检测详情
    viewDetail(row) {
      this.$router.push(`/admin/detection/detail/${row.id}`);
    }
  },
  beforeDestroy() {
    // 移除窗口大小变化监听器
    window.removeEventListener('resize', this.resizeCharts);
    
    // 销毁图表实例
    if (this.charts.weeklyTrend) {
      this.charts.weeklyTrend.dispose();
    }
    if (this.charts.resultDistribution) {
      this.charts.resultDistribution.dispose();
    }
  }
}
</script>

<style scoped>
.admin-dashboard {
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
  margin-bottom: 30px;
}

.data-card {
  position: relative;
  height: 170px;
  overflow: hidden;
  margin-bottom: 15px;
  transition: all 0.3s;
}

.data-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

.card-body {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 70px;
  padding: 0 15px;
}

.card-content {
  flex: 1;
  max-width: 70%;
  padding: 5px 0;
}

.card-value {
  font-size: 30px;
  font-weight: bold;
  margin-top: 5px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-icon {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 45px;
  height: 45px;
  border-radius: 50%;
  margin-left: 10px;
  background-color: rgba(64, 158, 255, 0.1);
}

.card-icon i {
  font-size: 24px;
  color: #409EFF;
}

.el-col:nth-child(1) .card-icon {
  background-color: rgba(103, 194, 58, 0.1);
}

.el-col:nth-child(1) .card-icon i {
  color: #67C23A;
}

.el-col:nth-child(2) .card-icon {
  background-color: rgba(64, 158, 255, 0.1);
}

.el-col:nth-child(2) .card-icon i {
  color: #409EFF;
}

.el-col:nth-child(3) .card-icon {
  background-color: rgba(245, 108, 108, 0.1);
}

.el-col:nth-child(3) .card-icon i {
  color: #F56C6C;
}

.el-col:nth-child(4) .card-icon {
  background-color: rgba(230, 162, 60, 0.1);
}

.el-col:nth-child(4) .card-icon i {
  color: #E6A23C;
}

.charts-row {
  margin-bottom: 30px;
}

.chart-card {
  margin-bottom: 20px;
  transition: all 0.3s;
}

.chart-card:hover {
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

.chart-container {
  height: 300px;
}

.recent-detections {
  margin-bottom: 20px;
  transition: all 0.3s;
}

.recent-detections:hover {
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

.pagination-container {
  text-align: right;
  margin-top: 20px;
}

/* 适配移动端 */
@media (max-width: 768px) {
  .card-value {
    font-size: 24px;
  }
  
  .card-icon i {
    font-size: 24px;
  }
  
  .chart-container {
    height: 250px;
  }

  .data-card {
    height: 120px;
  }
  
  .card-body {
    height: 60px;
  }
}
</style> 