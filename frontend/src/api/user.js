import axios from 'axios'

// 登录
export function login(data) {
  return axios.post('/users/token/', data)
}

// 获取用户信息
export function getUserInfo() {
  return axios.get('/users/me/')
}

// 注册
export function register(data) {
  return axios.post('/users/', data)
}

// 修改用户信息
export function updateUserInfo(id, data) {
  return axios.patch(`/users/${id}/`, data)
}

// 修改密码
export function changePassword(id, data) {
  return axios.post(`/users/${id}/change_password/`, data)
}

// 获取用户统计
export function getUserStats() {
  return axios.get('/users/stats/')
}
