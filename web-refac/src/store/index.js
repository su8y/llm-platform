import { createStore } from 'vuex'
import { addDays } from 'date-fns'

import { getUserInfo } from "@/api/user.js";
import { getCurrentCredit, getCurrentPlan } from "@/api/plan.js";

const now = new Date()

export default createStore({
  state: {
    userData: null,
    searchPeriod: {
      start: addDays(now, 6),
      end: now
    },
    planData: null,
    isPlanAlert: false,
    // isMobile: window.innerWidth < 768
    isMobile: navigator.userAgent.indexOf('Mobile') > -1,
    creditData: null,
    currentPage: 1,
    limitPage: 10,
    inboxSearchData: {
      subject: null,
      from: null,
      status: null,
      manager: null,
      startDate: null,
      endDate: null,
    },
    monitoringSearchData: {
      startDate: null,
      endDate: null,
      status: null,
      id: null,
      manager: null
    },
    referenceSearchData: {
      isOn: null,
      startDate: null,
      endDate: null,
      title: null,
      author: null,
      category: null
    },
    fileSearchData: {
      name: null,
      startDate: null,
      endDate: null
    },
    memberSearchData: {
      userId: null,
      department: null,
      emailAddress: null,
      status: null,
      authority: null,
      startDate: null,
      endDate: null
    },
    ragSearchData: {
      to: null,
      manager: null,
      subject: null,
      startDate: null,
      endDate: null,
    }
  },
  mutations: {
    setUserData (state, value) {
      state.userData = value
    },
    clearAllUserData (state) {
      state.userData = null
    },
    setSearchPeriod (state, value) {
      state.searchPeriod = value
    },
    setPlanData (state, value) {
      state.planData = value
    },
    setPlanAlert (state, value) {
      state.isPlanAlert = value
    },
    setIsMobile (state, value) {
      state.isMobile = value
    },
    setCreditData (state, value) {
      state.creditData = value
    },
    setPagination (state, value) {
      state.currentPage = value.newPage
      state.limitPage = value.newLimit
    },
    setInboxSearchData (state, value) {
      state.inboxSearchData = value
    },
    setMonitoringSearchData (state, value) {
      state.monitoringSearchData = value
    },
    setReferenceSearchData (state, value) {
      state.referenceSearchData = value
    },
    setFileSearchData (state, value) {
      state.fileSearchData = value
    },
    setMemberSearchData (state, value) {
      state.memberSearchData = value
    },
    setRagSearchData (state, value) {
      state.ragSearchData = value
    }
  },
  actions: {
    storeUserData ({ dispatch, commit }) {
      return getUserInfo().then(data => {
        commit('setUserData', data.data)
        return data.data
      })
    },
    storePlanData ({dispatch, commit}) {
      return getCurrentPlan().then(data => {
        commit('setPlanData', data.data)
        return data.data
      })
    },
    checkIsMobile ({ commit }) {
      // const isMobile = window.innerWidth < 768
      const isMobile = navigator.userAgent.indexOf('Mobile') > -1
      commit('setIsMobile', isMobile)
    },
    storeCreditData ({dispatch, commit}, payload = null) {
      const params = {
        params: {
          currentCredit: payload?.currentCredit || null
        }
      }

      return getCurrentCredit(params).then(data => {
        if (data.data) {
          commit('setCreditData', {data: data.data, code: data.code})
        }
        return {
          data: data.data,
          code: data.code
        }
      })
    }
  }
})
