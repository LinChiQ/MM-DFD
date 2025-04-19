import axios from 'axios'

const state = {
  detectionHistory: [],
  currentDetection: null,
  stats: {
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

const mutations = {
  SET_DETECTION_HISTORY: (state, history) => {
    state.detectionHistory = history
  },
  SET_CURRENT_DETECTION: (state, detection) => {
    state.currentDetection = detection
  },
  ADD_DETECTION: (state, detection) => {
    state.detectionHistory.unshift(detection)
  },
  SET_STATS: (state, stats) => {
    state.stats = stats
  }
}

const actions = {
  // 获取检测历史
  getDetectionHistory({ commit }) {
    return new Promise((resolve, reject) => {
      axios.get('/detection/detections/my_detections/')
        .then(response => {
          const history = response.data.results || response.data
          commit('SET_DETECTION_HISTORY', history)
          resolve(history)
        })
        .catch(error => {
          reject(error)
        })
    })
  },

  // 获取检测详情
  getDetectionDetail({ commit }, id) {
    console.log(`Fetching detection detail for ID: ${id}`);
    if (!id || id === 'undefined') {
      console.error('Attempted to fetch detail with invalid ID:', id);
      return Promise.reject(new Error('Invalid ID for detection detail'));
    }
    return new Promise((resolve, reject) => {
      axios.get(`/detection/detections/${id}/`)
        .then(response => {
          console.log('Backend response from getDetectionDetail:', response.data);
          commit('SET_CURRENT_DETECTION', response.data)
          resolve(response.data)
        })
        .catch(error => {
          console.error(`getDetectionDetail API call failed for ID ${id}:`, error.response || error);
          reject(error)
        })
    })
  },

  // 创建新检测
  createDetection({ commit }, detectionData) {
    return new Promise((resolve, reject) => {
      const formData = new FormData()
      formData.append('title', detectionData.title)
      formData.append('content', detectionData.content)
      if (detectionData.image) {
        formData.append('image', detectionData.image)
      }
      
      axios.post('/detection/detections/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
        .then(response => {
          console.log('Backend response from createDetection:', response.data);
          commit('ADD_DETECTION', response.data)
          commit('SET_CURRENT_DETECTION', response.data)
          resolve(response.data)
        })
        .catch(error => {
          console.error('createDetection API call failed:', error.response || error);
          reject(error)
        })
    })
  },

  // 获取检测结果
  getDetectionResult({ commit }, id) {
    return new Promise((resolve, reject) => {
      axios.get(`/detection/detections/${id}/result/`)
        .then(response => {
          commit('SET_CURRENT_DETECTION', response.data)
          resolve(response.data)
        })
        .catch(error => {
          reject(error)
        })
    })
  },

  // 获取检测统计信息
  getDetectionStats({ commit }, isAdmin = false) {
    return new Promise((resolve, reject) => {
      const url = `/detection/detections/get_stats/${isAdmin ? '?all=true' : ''}`
      axios.get(url)
        .then(response => {
          commit('SET_STATS', response.data)
          resolve(response.data)
        })
        .catch(error => {
          reject(error)
        })
    })
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions
}
