// src/store/index.js
import { createStore } from 'vuex'

export default createStore({
  state: {
    user: null,
    isLoggedIn: false
  },
  getters: {
    isAuthenticated: state => state.isLoggedIn,
    userEmail: state => state.user ? state.user.email : ''
  },
  mutations: {
    setUser(state, user) {
      state.user = user
      state.isLoggedIn = !!user
    }
  },
  actions: {
    login({ commit }, user) {
      // Логика авторизации
      commit('setUser', user)
    },
    logout({ commit }) {
      // Логика выхода
      commit('setUser', null)
    }
  }
})
