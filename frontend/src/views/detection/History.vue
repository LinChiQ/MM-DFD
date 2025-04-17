<template>
  <div class="history-container">
    <div class="page-title">检测历史</div>
    
    <el-card shadow="hover">
      <div class="filter-container">
        <el-input
          placeholder="搜索标题"
          v-model="searchQuery"
          style="width: 200px;"
          clearable
          @clear="handleFilter"
          @keyup.enter.native="handleFilter"
        >
          <i slot="prefix" class="el-input__icon el-icon-search"></i>
        </el-input>
        
        <el-select v-model="statusFilter" placeholder="状态" clearable style="width: 120px;" @change="handleFilter">
          <el-option
            v-for="item in statusOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value">
          </el-option>
        </el-select>
        
        <el-select v-model="resultFilter" placeholder="结果" clearable style="width: 120px;" @change="handleFilter">
          <el-option
            v-for="item in resultOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value">
          </el-option>
        </el-select>
        
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 300px;"
          @change="handleFilter"
        >
        </el-date-picker>
        
        <el-button class="filter-item" type="primary" icon="el-icon-search" @click="handleFilter">
          搜索
        </el-button>
      </div>
      
      <el-table
        :data="filteredDetections"
        style="width: 100%; margin-top: 20px;"
        v-loading="loading"
        border
      >
        <el-table-column
          prop="title"
          label="标题"
          min-width="200"
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
      
      <div class="pagination-container">
        <el-pagination
          background
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="currentPage"
          :page-sizes="[10, 20, 30, 50]"
          :page-size="pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="totalItems">
        </el-pagination>
      </div>
    </el-card>
  </div>
</template>

<script>
export default {
  name: 'DetectionHistory',
  data() {
    return {
      loading: false,
      searchQuery: '',
      statusFilter: '',
      resultFilter: '',
      dateRange: [],
      currentPage: 1,
      pageSize: 10,
      
      statusOptions: [
        { value: 'completed', label: '完成' },
        { value: 'pending', label: '等待中' },
        { value: 'processing', label: '处理中' },
        { value: 'failed', label: '失败' }
      ],
      resultOptions: [
        { value: true, label: '真实' },
        { value: false, label: '虚假' }
      ]
    }
  },
  computed: {
    detectionHistory() {
      return this.$store.getters.detectionHistory || []
    },
    filteredData() {
      let filteredData = [...this.detectionHistory]
      
      // 应用标题搜索
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase()
        filteredData = filteredData.filter(item => 
          item.title.toLowerCase().includes(query)
        )
      }
      
      // 应用状态过滤
      if (this.statusFilter) {
        filteredData = filteredData.filter(item => 
          item.status === this.statusFilter
        )
      }
      
      // 应用结果过滤
      if (this.resultFilter !== '') {
        filteredData = filteredData.filter(item => 
          item.result === this.resultFilter
        )
      }
      
      // 应用日期范围过滤
      if (this.dateRange && this.dateRange.length === 2) {
        const startDate = new Date(this.dateRange[0])
        startDate.setHours(0, 0, 0, 0)
        const endDate = new Date(this.dateRange[1])
        endDate.setHours(23, 59, 59, 999)
        
        filteredData = filteredData.filter(item => {
          const itemDate = new Date(item.created_at)
          return itemDate >= startDate && itemDate <= endDate
        })
      }
      
      return filteredData
    },
    totalItems() {
      return this.filteredData.length
    },
    filteredDetections() {
      // 分页
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      return this.filteredData.slice(start, end)
    }
  },
  mounted() {
    this.fetchData()
  },
  methods: {
    fetchData() {
      this.loading = true
      this.$store.dispatch('detection/getDetectionHistory')
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
    
    handleFilter() {
      this.currentPage = 1
    },
    
    handleSizeChange(val) {
      this.pageSize = val
    },
    
    handleCurrentChange(val) {
      this.currentPage = val
    },
    
    viewDetail(id) {
      this.$router.push(`/detection/detail/${id}`)
    }
  }
}
</script>

<style lang="scss" scoped>
@import "@/assets/css/variables.scss";

.history-container {
  padding: 20px;
}

.filter-container {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 10px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style> 