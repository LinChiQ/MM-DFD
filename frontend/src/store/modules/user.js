import axios from 'axios'
import router from '@/router'
import Cookies from 'js-cookie'

const TOKEN_KEY = 'mm_dfd_token'
const USER_KEY = 'mm_dfd_user'

const state = {
  token: Cookies.get(TOKEN_KEY),
  user: JSON.parse(localStorage.getItem(USER_KEY) || '{}'),
  roles: []
}

const mutations = {
  SET_TOKEN: (state, token) => {
    state.token = token
  },
  SET_USER: (state, user) => {
    state.user = user
  },
  SET_ROLES: (state, roles) => {
    state.roles = roles
  }
}

const actions = {
  // 用户登录
  login({ commit }, userInfo) {
    const { username, password } = userInfo
    return new Promise((resolve, reject) => {
      axios.post('/users/token/', { username, password })
        .then(response => {
          const { access } = response.data
          commit('SET_TOKEN', access)
          Cookies.set(TOKEN_KEY, access, { expires: 7 }) // 保存7天
          resolve()
        })
        .catch(error => {
          reject(error)
        })
    })
  },

  // 获取用户信息
  getUserInfo({ commit }) {
    return new Promise((resolve, reject) => {
      axios.get('/users/me/')
        .then(response => {
          const user = response.data
          commit('SET_USER', user)
          localStorage.setItem(USER_KEY, JSON.stringify(user))
          
          // 设置用户角色
          const roles = ['user']
          if (user.is_staff) {
            roles.push('admin')
          }
          commit('SET_ROLES', roles)
          resolve(user)
        })
        .catch(error => {
          reject(error)
        })
    })
  },

  // 用户注册
  register({}, userInfo) {
    return new Promise((resolve, reject) => {
      axios.post('/users/', userInfo)
        .then(response => {
          resolve(response.data)
        })
        .catch(error => {
          reject(error)
        })
    })
  },

  // 更新用户信息
  updateUserInfo({ commit, state }, userInfo) {
    return new Promise((resolve, reject) => {
      axios.patch(`/users/${state.user.id}/`, userInfo)
        .then(response => {
          const updatedUser = { ...state.user, ...response.data }
          commit('SET_USER', updatedUser)
          localStorage.setItem(USER_KEY, JSON.stringify(updatedUser))
          resolve(updatedUser)
        })
        .catch(error => {
          reject(error)
        })
    })
  },

  // 修改密码
  changePassword({ state }, passwordInfo) {
    return new Promise((resolve, reject) => {
      axios.post(`/users/${state.user.id}/change_password/`, passwordInfo)
        .then(response => {
          resolve(response.data)
        })
        .catch(error => {
          reject(error)
        })
    })
  },

  // 用户登出
  logout({ commit }) {
    commit('SET_TOKEN', '')
    commit('SET_USER', {})
    commit('SET_ROLES', [])
    Cookies.remove(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    router.push('/login')
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions
}
