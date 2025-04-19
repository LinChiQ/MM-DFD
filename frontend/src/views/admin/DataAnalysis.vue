<template>
  <div class="data-analysis">
    <div class="page-header">
      <h1 class="page-title">数据分析</h1>
      <div class="time-filter">
        <el-radio-group v-model="timeRange" size="small" @change="handleTimeRangeChange">
          <el-radio-button label="today">今日</el-radio-button>
          <el-radio-button label="week">本周</el-radio-button>
          <el-radio-button label="month">本月</el-radio-button>
          <el-radio-button label="year">本年</el-radio-button>
        </el-radio-group>
        <el-date-picker
          v-model="customDateRange"
          type="daterange"
          size="small"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="yyyy-MM-dd"
          value-format="yyyy-MM-dd"
          @change="handleCustomDateChange">
        </el-date-picker>
      </div>
    </div>
    
    <!-- 数据概览卡片 -->
    <el-row :gutter="20" class="data-overview">
      <el-col :span="6">
        <el-card shadow="hover" class="overview-card">
          <div class="overview-icon" style="background-color: #409EFF">
            <i class="el-icon-s-data"></i>
          </div>
          <div class="overview-content">
            <div class="overview-title">总检测次数</div>
            <div class="overview-value">{{ statistics.totalDetections }}</div>
            <div class="overview-change" :class="{'up': statistics.detectionChange > 0, 'down': statistics.detectionChange < 0}">
              <i :class="statistics.detectionChange >= 0 ? 'el-icon-top' : 'el-icon-bottom'"></i>
              {{ Math.abs(statistics.detectionChange) }}%
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="overview-card">
          <div class="overview-icon" style="background-color: #67C23A">
            <i class="el-icon-user"></i>
          </div>
          <div class="overview-content">
            <div class="overview-title">活跃用户数</div>
            <div class="overview-value">{{ statistics.activeUsers }}</div>
            <div class="overview-change" :class="{'up': statistics.userChange > 0, 'down': statistics.userChange < 0}">
              <i :class="statistics.userChange >= 0 ? 'el-icon-top' : 'el-icon-bottom'"></i>
              {{ Math.abs(statistics.userChange) }}%
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="overview-card">
          <div class="overview-icon" style="background-color: #E6A23C">
            <i class="el-icon-warning"></i>
          </div>
          <div class="overview-content">
            <div class="overview-title">假新闻检出率</div>
            <div class="overview-value">{{ statistics.fakeNewsRate }}%</div>
            <div class="overview-change" :class="{'up': statistics.fakeNewsChange > 0, 'down': statistics.fakeNewsChange < 0}">
              <i :class="statistics.fakeNewsChange >= 0 ? 'el-icon-top' : 'el-icon-bottom'"></i>
              {{ Math.abs(statistics.fakeNewsChange) }}%
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="overview-card">
          <div class="overview-icon" style="background-color: #F56C6C">
            <i class="el-icon-pie-chart"></i>
          </div>
          <div class="overview-content">
            <div class="overview-title">平均置信度</div>
            <div class="overview-value">{{ statistics.avgConfidence }}%</div>
            <div class="overview-change" :class="{'up': statistics.confidenceChange > 0, 'down': statistics.confidenceChange < 0}">
              <i :class="statistics.confidenceChange >= 0 ? 'el-icon-top' : 'el-icon-bottom'"></i>
              {{ Math.abs(statistics.confidenceChange) }}%
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-container">
      <el-col :span="16">
        <el-card shadow="hover" class="chart-card">
          <div slot="header" class="clearfix">
            <span>检测趋势</span>
            <el-radio-group v-model="trendChartType" size="mini" style="float: right">
              <el-radio-button label="day">日</el-radio-button>
              <el-radio-button label="week">周</el-radio-button>
              <el-radio-button label="month">月</el-radio-button>
            </el-radio-group>
          </div>
          <div class="chart" ref="trendChart"></div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card shadow="hover" class="chart-card">
          <div slot="header" class="clearfix">
            <span>检测结果分布</span>
          </div>
          <div class="chart" ref="pieChart"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="chart-container">
      <el-col :span="12">
        <el-card shadow="hover" class="chart-card">
          <div slot="header" class="clearfix">
            <span>用户活跃度排行</span>
          </div>
          <div class="chart" ref="userRankChart"></div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card shadow="hover" class="chart-card">
          <div slot="header" class="clearfix">
            <span>检测内容分类统计</span>
          </div>
          <div class="chart" ref="categoryChart"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 热门检测内容列表 -->
    <el-card shadow="hover" class="list-card">
      <div slot="header" class="clearfix">
        <span>热门检测内容</span>
        <el-button style="float: right; padding: 3px 0" type="text" @click="viewAllDetections">查看全部</el-button>
      </div>
      
      <el-table :data="hotDetections" style="width: 100%">
        <el-table-column prop="content" label="检测内容" min-width="300">
          <template slot-scope="scope">
            <div class="content-ellipsis">{{ scope.row.content }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="user" label="用户" width="120"></el-table-column>
        <el-table-column prop="time" label="检测时间" width="180"></el-table-column>
        <el-table-column prop="result" label="检测结果" width="100">
          <template slot-scope="scope">
            <el-tag :type="scope.row.result === '真实' ? 'success' : 'danger'">
              {{ scope.row.result }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="confidence" label="置信度" width="100">
          <template slot-scope="scope">
            <el-progress :percentage="scope.row.confidence" :color="getConfidenceColor(scope.row.confidence)"></el-progress>
          </template>
        </el-table-column>
        <el-table-column prop="count" label="检测次数" width="100" sortable></el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
// 引入echarts
import * as echarts from 'echarts';

export default {
  name: 'DataAnalysis',
  data() {
    return {
      // 时间筛选
      timeRange: 'month',
      customDateRange: [],
      
      // 图表类型
      trendChartType: 'day',
      
      // 统计数据
      statistics: {
        totalDetections: 8526,
        detectionChange: 13.5,
        activeUsers: 742,
        userChange: 8.2,
        fakeNewsRate: 37.8,
        fakeNewsChange: -2.3,
        avgConfidence: 82.6,
        confidenceChange: 1.4
      },
      
      // 图表实例
      trendChart: null,
      pieChart: null,
      userRankChart: null,
      categoryChart: null,
      
      // 热门检测内容
      hotDetections: []
    };
  },
  mounted() {
    this.initCharts();
    this.generateMockData();
  },
  methods: {
    // 初始化所有图表
    initCharts() {
      this.$nextTick(() => {
        // 检测趋势图
        this.trendChart = echarts.init(this.$refs.trendChart);
        
        // 检测结果饼图
        this.pieChart = echarts.init(this.$refs.pieChart);
        
        // 用户活跃度排行图
        this.userRankChart = echarts.init(this.$refs.userRankChart);
        
        // 检测内容分类统计图
        this.categoryChart = echarts.init(this.$refs.categoryChart);
        
        // 设置响应式
        window.addEventListener('resize', this.resizeCharts);
        
        // 初始化图表数据
        this.updateCharts();
      });
    },
    
    // 更新所有图表
    updateCharts() {
      this.updateTrendChart();
      this.updatePieChart();
      this.updateUserRankChart();
      this.updateCategoryChart();
    },
    
    // 更新趋势图
    updateTrendChart() {
      // 生成日期数据
      const days = 30;
      const dateList = [];
      const realData = [];
      const fakeData = [];
      
      for (let i = 0; i < days; i++) {
        const date = new Date();
        date.setDate(date.getDate() - (days - i - 1));
        const dateStr = `${date.getMonth() + 1}/${date.getDate()}`;
        dateList.push(dateStr);
        
        // 生成随机数据
        const realCount = Math.floor(Math.random() * 100) + 50;
        const fakeCount = Math.floor(Math.random() * 80) + 20;
        
        realData.push(realCount);
        fakeData.push(fakeCount);
      }
      
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        legend: {
          data: ['真实新闻', '虚假新闻'],
          right: 10,
          top: 10
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: dateList,
          axisTick: {
            alignWithLabel: true
          }
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            name: '真实新闻',
            type: 'line',
            smooth: true,
            data: realData,
            itemStyle: {
              color: '#67C23A'
            },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(103, 194, 58, 0.5)' },
                { offset: 1, color: 'rgba(103, 194, 58, 0.1)' }
              ])
            }
          },
          {
            name: '虚假新闻',
            type: 'line',
            smooth: true,
            data: fakeData,
            itemStyle: {
              color: '#F56C6C'
            },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(245, 108, 108, 0.5)' },
                { offset: 1, color: 'rgba(245, 108, 108, 0.1)' }
              ])
            }
          }
        ]
      };
      
      this.trendChart.setOption(option);
    },
    
    // 更新饼图
    updatePieChart() {
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b} : {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 'left',
          data: ['真实新闻', '虚假新闻', '可疑内容', '无法判断']
        },
        series: [
          {
            name: '检测结果',
            type: 'pie',
            radius: '60%',
            center: ['60%', '50%'],
            data: [
              { value: 62, name: '真实新闻', itemStyle: { color: '#67C23A' } },
              { value: 25, name: '虚假新闻', itemStyle: { color: '#F56C6C' } },
              { value: 10, name: '可疑内容', itemStyle: { color: '#E6A23C' } },
              { value: 3, name: '无法判断', itemStyle: { color: '#909399' } }
            ],
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            },
            label: {
              formatter: '{b}: {d}%'
            }
          }
        ]
      };
      
      this.pieChart.setOption(option);
    },
    
    // 更新用户排行图
    updateUserRankChart() {
      const userNames = ['张三', '李四', '王五', '赵六', '钱七', '孙八', '周九', '吴十'];
      const userValues = [98, 89, 76, 72, 63, 58, 45, 32];
      
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
          type: 'value',
          boundaryGap: [0, 0.01]
        },
        yAxis: {
          type: 'category',
          data: userNames.reverse(),
          axisLabel: {
            interval: 0
          }
        },
        series: [
          {
            name: '检测次数',
            type: 'bar',
            data: userValues.reverse(),
            itemStyle: {
              color: function(params) {
                const colorList = ['#409EFF', '#53a8ff', '#66b1ff', '#79bbff', '#8cc5ff', '#a0cfff', '#b3d8ff', '#c6e2ff'];
                return colorList[params.dataIndex];
              }
            }
          }
        ]
      };
      
      this.userRankChart.setOption(option);
    },
    
    // 更新内容分类图
    updateCategoryChart() {
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b} : {c}'
        },
        radar: {
          radius: '60%',
          center: ['50%', '50%'],
          name: {
            textStyle: {
              color: '#333',
              backgroundColor: '#fff',
              borderRadius: 3,
              padding: [3, 5]
            }
          },
          indicator: [
            { name: '政治新闻', max: 100 },
            { name: '社会新闻', max: 100 },
            { name: '经济新闻', max: 100 },
            { name: '体育新闻', max: 100 },
            { name: '娱乐新闻', max: 100 },
            { name: '科技新闻', max: 100 }
          ]
        },
        series: [
          {
            name: '检测分类',
            type: 'radar',
            areaStyle: {
              color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
                { offset: 0, color: 'rgba(64, 158, 255, 0.7)' },
                { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
              ])
            },
            data: [
              {
                value: [85, 76, 62, 48, 92, 70],
                name: '检测数量',
                itemStyle: {
                  color: '#409EFF'
                },
                lineStyle: {
                  color: '#409EFF'
                }
              }
            ]
          }
        ]
      };
      
      this.categoryChart.setOption(option);
    },
    
    // 响应式调整图表大小
    resizeCharts() {
      this.trendChart && this.trendChart.resize();
      this.pieChart && this.pieChart.resize();
      this.userRankChart && this.userRankChart.resize();
      this.categoryChart && this.categoryChart.resize();
    },
    
    // 生成模拟数据
    generateMockData() {
      // 生成热门检测内容
      const contentList = [
        '研究显示喝咖啡有助于延长寿命',
        '某国科学家发现可再生能源新突破',
        '国家将出台新政策支持人工智能发展',
        '新冠病毒变种可能在冬季再次爆发',
        '世界杯小组赛爆出冷门，前冠军被淘汰',
        '研究发现常见食品添加剂可能致癌',
        '科学家在火星发现疑似生命痕迹',
        '某公司CEO涉嫌财务造假被调查',
        '政府宣布将投入100亿建设智慧城市',
        '气象部门预测今年将有极端天气事件增多'
      ];
      
      const users = ['张三', '李四', '王五', '赵六', '钱七'];
      const results = ['真实', '虚假'];
      
      this.hotDetections = contentList.map((content, index) => {
        const now = new Date();
        const randomDays = Math.floor(Math.random() * 30);
        const randomHours = Math.floor(Math.random() * 24);
        const randomMinutes = Math.floor(Math.random() * 60);
        
        now.setDate(now.getDate() - randomDays);
        now.setHours(now.getHours() - randomHours);
        now.setMinutes(now.getMinutes() - randomMinutes);
        
        const timeStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
        
        const result = results[Math.floor(Math.random() * results.length)];
        const confidence = Math.floor(Math.random() * 30) + 70;
        
        return {
          id: index + 1,
          content,
          user: users[Math.floor(Math.random() * users.length)],
          time: timeStr,
          result,
          confidence,
          count: Math.floor(Math.random() * 50) + 10
        };
      });
      
      // 按检测次数排序
      this.hotDetections.sort((a, b) => b.count - a.count);
    },
    
    // 处理时间范围变化
    handleTimeRangeChange() {
      // 清空自定义日期范围
      this.customDateRange = [];
      this.updateCharts();
    },
    
    // 处理自定义日期变化
    handleCustomDateChange() {
      if (this.customDateRange && this.customDateRange.length === 2) {
        this.timeRange = 'custom';
        this.updateCharts();
      }
    },
    
    // 获取置信度颜色
    getConfidenceColor(confidence) {
      if (confidence < 60) return '#F56C6C';
      if (confidence < 75) return '#E6A23C';
      if (confidence < 90) return '#67C23A';
      return '#409EFF';
    },
    
    // 查看所有检测
    viewAllDetections() {
      this.$message.info('跳转到所有检测记录页面');
      // 实际开发中这里应该是路由跳转
      // this.$router.push('/admin/detection-records');
    }
  },
  beforeDestroy() {
    // 移除窗口大小改变事件
    window.removeEventListener('resize', this.resizeCharts);
    
    // 销毁图表实例
    this.trendChart && this.trendChart.dispose();
    this.pieChart && this.pieChart.dispose();
    this.userRankChart && this.userRankChart.dispose();
    this.categoryChart && this.categoryChart.dispose();
  }
};
</script>

<style lang="scss" scoped>
.data-analysis {
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
    
    .time-filter {
      display: flex;
      align-items: center;
      gap: 15px;
    }
  }
  
  .data-overview {
    margin-bottom: 20px;
    
    .overview-card {
      height: 120px;
      display: flex;
      align-items: center;
      padding: 20px;
      
      .overview-icon {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        margin-right: 15px;
        
        i {
          font-size: 28px;
          color: #fff;
        }
      }
      
      .overview-content {
        flex: 1;
        
        .overview-title {
          font-size: 14px;
          color: #909399;
          margin-bottom: 8px;
        }
        
        .overview-value {
          font-size: 24px;
          font-weight: bold;
          color: #303133;
          margin-bottom: 8px;
        }
        
        .overview-change {
          font-size: 12px;
          
          &.up {
            color: #67C23A;
          }
          
          &.down {
            color: #F56C6C;
          }
          
          i {
            margin-right: 2px;
          }
        }
      }
    }
  }
  
  .chart-container {
    margin-bottom: 20px;
    
    .chart-card {
      .chart {
        height: 350px;
      }
    }
  }
  
  .list-card {
    margin-bottom: 20px;
    
    .content-ellipsis {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 300px;
    }
  }
}
</style> 