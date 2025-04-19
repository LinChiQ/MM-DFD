const getters = {
  // 用户信息
  token: state => state.user.token,
  user: state => state.user.user,
  roles: state => state.user.roles,
  isAdmin: state => state.user.user ? state.user.user.is_staff : false,
  currentUser: state => state.user.user,
  
  // 检测相关
  detectionHistory: state => state.detection.detectionHistory,
  detectionStats: state => state.detection.stats,
  detections: state => state.detection.list,
  detectionCount: state => state.detection.count,
  currentDetection: state => state.detection.currentDetection
}

export default getters 