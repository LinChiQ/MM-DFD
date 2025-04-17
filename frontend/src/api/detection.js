import axios from 'axios'

// 获取检测历史
export function getDetectionHistory() {
  return axios.get('/detection/my_detections/')
}

// 获取检测详情
export function getDetectionDetail(id) {
  return axios.get(`/detection/${id}/`)
}

// 创建新检测
export function createDetection(data) {
  const formData = new FormData()
  formData.append('title', data.title)
  formData.append('content', data.content)
  
  if (data.image) {
    formData.append('image', data.image)
  }
  
  return axios.post('/detection/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 获取检测结果
export function getDetectionResult(id) {
  return axios.get(`/detection/${id}/result/`)
}

// 获取检测统计信息
export function getDetectionStats(isAdmin = false) {
  const url = isAdmin ? '/detection/get_stats/?all=true' : '/detection/get_stats/'
  return axios.get(url)
}
