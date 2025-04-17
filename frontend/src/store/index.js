import Vue from 'vue'
import Vuex from 'vuex'
import user from './modules/user'
import detection from './modules/detection'
import getters from './getters'

Vue.use(Vuex)

const store = new Vuex.Store({
  modules: {
    user,
    detection
  },
  getters
})

export default store
