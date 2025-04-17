const getters = {
  // 用户信息
  token: state => state.user.token,
  user: state => state.user.user,
  roles: state => state.user.roles,
  
  // 检测相关
  detectionHistory: state => state.detection.detectionHistory,
  detectionStats: state => state.detection.stats,
  currentDetection: state => state.detection.currentDetection
}

export default getters 