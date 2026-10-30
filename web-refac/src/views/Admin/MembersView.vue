<script setup>
import { reactive, ref, onBeforeMount, inject } from "vue"
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'

import { changeUserAuth, deleteUser, getAuthNameList, getMembersList, inviteMember, reInviteMember } from '@/api/admin.js'
import { dateFormatter } from "@/libs/utils.js";
import { HTTP_CODES, SEND_MAIL_TYPE, WARNING_TYPE } from "@/libs/constants.js";

import AdminMembers from "@/components/Admin/AdminMembers.vue"
import Loading from "@/components/Modal/Loading.vue";
import Warning from "@/components/Modal/Warning.vue";
import SendMail from "@/components/Modal/SendMail.vue";

const modal = inject('$modal')
const router = useRouter()
const store = useStore()

const membersData = ref([])
const authNameList = ref([])
const searchFilter = reactive({
  userId: store.state.memberSearchData.userId ? store.state.memberSearchData.userId : '',
  department: store.state.memberSearchData.department ? store.state.memberSearchData.department : '',
  emailAddress: store.state.memberSearchData.emailAddress ? store.state.memberSearchData.emailAddress : '',
  status: store.state.memberSearchData.status ? store.state.memberSearchData.status : 'all',
  authority: store.state.memberSearchData.authority ? store.state.memberSearchData.authority : 'all'
})
const dateRange = reactive({
  start: store.state.memberSearchData.startDate ? store.state.memberSearchData.startDate : null,
  end: store.state.memberSearchData.endDate ? store.state.memberSearchData.endDate : null,
})
const page = reactive({
  totalLength: 0,
  limit: 10,
  currentPage: store.state.currentPage ? parseInt(store.state.currentPage) : 1,
  selectedOption: store.state.limitPage ? parseInt(store.state.limitPage) : 10
})

onBeforeMount(async () => {
  await getMembersListData()
})

const getMembersListData = async () => {
  modal.open(Loading)

  const params = {
    page: page.currentPage,
    perPage: page.selectedOption,
    userId: searchFilter.userId,
    department: searchFilter.department,
    emailAddress: searchFilter.emailAddress,
    status: searchFilter.status,
    authName: searchFilter.authority,
    startDate: dateRange.start && dateFormatter(dateRange.start),
    endDate: dateRange.end && dateFormatter(dateRange.end)
  }

  try {
    const res = await getMembersList(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      membersData.value = res.data.rows
      page.totalLength = res.data.count
      page.limit = page.selectedOption
      modal.close(Loading)
    } else {
      membersData.value = null
      page.totalLength = 0
      modal.close(Loading)
      alert(res.message)
      console.log('Error: ', res)
    }
  } catch (e) {
    modal.close(Loading)
    console.error('Error: ', e)
  }
}


const sendInviteMail = async (params) => {
  modal.open(Loading)

  try {
    const res = await inviteMember(params)

    switch (res.code) {
      case HTTP_CODES.DUPLICATED.EMAIL:
        modal.close()
        modal.open(Warning, WARNING_TYPE.DUPLICATED_EMAIL)
        break
      case HTTP_CODES.INVALID_EMAIL:
        modal.close()
        modal.open(Warning, WARNING_TYPE.INVALID_EMAIL)
        break
      default:
        modal.close()
        await modal.open(SendMail, SEND_MAIL_TYPE.SEND_INVITE).then(() => {
          window.location.reload()
        })
        break
    }

  } catch (e) {
    modal.close(Loading)
    alert(e.response.data.message)
    console.log('Error: ', e)
  }
}

const resendInviteMail = async (params) => {
  modal.open(Loading)

  try {
    const res = await reInviteMember(params)

    switch (res.code) {
      case HTTP_CODES.DUPLICATED.EMAIL:
        modal.close()
        modal.open(Warning, WARNING_TYPE.DUPLICATED_RE_INVITE)
        break
      case HTTP_CODES.INVALID_EMAIL:
        modal.close()
        modal.open(Warning, WARNING_TYPE.DUPLICATED_RE_INVITE)
        break
      default:
        modal.close()
        await modal.open(SendMail, SEND_MAIL_TYPE.SEND_INVITE).then(() => {
          window.location.reload()
        })
        break
    }

  } catch (e) {
    modal.close(Loading)
    alert(e.response.data.message)
    console.log('Error: ', e)
  }
}

const deleteUserData = async (params) => {
  try {
    await modal.open(Warning, WARNING_TYPE.SECESSION).then(async () => {
      modal.close()

      const res = await deleteUser(params)

      if (res.code === HTTP_CODES.SUCCESS) {
        router.go(0)
      } else {
        alert(res)
        console.log('Error: ', res)
      }
    }).catch(() => {
      modal.close()
    })
  } catch (e) {
    alert(e)
    console.error('Error: ', e)
    modal.close()
  }
}

const openMemberAuthority = async () => {
  try {
    const res = await getAuthNameList()

    if (res.code === HTTP_CODES.SUCCESS) {
      authNameList.value = res.data
    } else {
      alert(res.message)
      console.log('Error: ', res)
    }

  } catch (e) {
    alert(e)
    console.log('Error: ', e)
  }
}

const selectMemAuthority = async (params) => {
  try {
    await modal.open(Warning, WARNING_TYPE.AUTHORITY).then(async () => {
      modal.close()

      const res = await changeUserAuth(params)

      if (res.code === HTTP_CODES.SUCCESS) {
        router.go(0)
      } else {
        alert(res.message)
        console.log('Error: ', res)
      }
    }).catch(() => {
      modal.close()
    })
  } catch (e){
    modal.close()
    console.error('Error: ', e)
  }
}

/**
 *
 * @param {string} type
 * @param {string|number|Object} value
 * @returns {Promise<void>}
 */
const changeOption = async (type, value) => {
  switch (type) {
    case 'current':
      page.currentPage = value
      break
    case 'pageOption':
      page.selectedOption = value
      page.currentPage = 1
      break
    case 'email':
      await sendInviteMail(value)
      break
    case 'delete':
      await deleteUserData(value)
      break
    case 'resend':
      await resendInviteMail(value)
      break
    case 'authority':
      await selectMemAuthority(value)
      break
  }

  if (type !== 'resend' && type !== 'email') {
    await getMembersListData()
  }
}

/**
 *
 * @param {string} type
 * @param {string} value
 */
const searchOption = (type, value) => {
  switch (type) {
    case 'status':
      searchFilter.status = value
      break
    case 'authority':
      searchFilter.authority = value
      break
    case 'email':
      searchFilter.emailAddress = value
      break
    case 'department':
      searchFilter.department = value
      break
    case 'id':
      searchFilter.userId = value
      break
  }
}

const dateOption = (start, end) => {
  dateRange.start = start
  dateRange.end = end
}

const onSearch = async () => {
  store.commit('setPagination', {
    newPage: 1,
    newLimit: page.selectedOption
  })
  page.currentPage = 1

  store.commit('setMemberSearchData', {
    userId: searchFilter.userId,
    department: searchFilter.department,
    emailAddress: searchFilter.emailAddress,
    status: searchFilter.status === 'all' ? '' : searchFilter.status,
    authority: searchFilter.authority === 'all' ? '' : searchFilter.authority,
    startDate: dateRange.start,
    endDate: dateRange.end
  })

  await getMembersListData()
}
</script>

<template>
  <AdminMembers
      :members-data="membersData"
      :page="page"
      :search-filter="searchFilter"
      :date-range="dateRange"
      :auth-name-list="authNameList"
      @change="changeOption"
      @searchChange="searchOption"
      @dateChange="dateOption"
      @openList="openMemberAuthority"
      @search="onSearch"
  />
</template>
