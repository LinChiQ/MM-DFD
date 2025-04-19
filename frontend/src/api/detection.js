import axios from 'axios'

// 获取检测历史
export function getDetectionHistory() {
  return axios.get('/detection/detections/my_detections/')
}

// 获取检测详情
export function getDetectionDetail(id) {
  return axios.get(`/detection/detections/${id}/`)
}

// 创建新检测
export function createDetection(data) {
  const formData = new FormData()
  formData.append('title', data.title)
  formData.append('content', data.content)
  
  if (data.image) {
    formData.append('image', data.image)
  }
  
  return axios.post('/detection/detections/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 获取检测结果
export function getDetectionResult(id) {
  return axios.get(`/detection/detections/${id}/result/`)
}

// 获取检测统计信息
export function getDetectionStats(isAdmin = false) {
  const url = isAdmin ? '/detection/detections/get_stats/?all=true' : '/detection/detections/get_stats/'
  return axios.get(url)
}

// 删除检测记录
export function deleteDetection(id) {
  return axios.delete(`/detection/detections/${id}/`, {
    headers: {
      'X-CSRFToken': document.cookie.replace(/(?:(?:^|.*;\s*)csrftoken\s*=\s*([^;]*).*$)|^.*$/, '$1')
    }
  })
}
