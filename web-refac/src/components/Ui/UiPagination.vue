<script setup>
import { defineProps, defineEmits, computed, watch } from "vue";
import { useStore } from "vuex";

// Props 및 이벤트 정의
const emit = defineEmits(["changePage"]);
const props = defineProps({
  total: {
    type: Number, // 전체 아이템 수
    default: null
  },
  currentPage: {
    type: Number, // 현재 페이지 번호
    default: 1
  },
  limit: {
    type: Number, // 페이지당 아이템 수
    default: 10
  },
  defaultPages: {
    type: Number,
    default: 5
  },
})

const store = useStore();

// 전체 페이지 수 계산
const totalPage = computed(() => {
  return Math.ceil(props.total / props.limit);
});

// 첫 번째 페이지 번호 계산
const firstPage = computed(() => {
  return (pageGroup.value - 1) * props.defaultPages + 1;
});

// 마지막 페이지 번호 계산
const lastPage = computed(() => {
  return Math.min(pageGroup.value * props.defaultPages, totalPage.value);
});

// 페이지 그룹 계산 (5페이지 단위)
const pageGroup = computed(() => {
  return Math.ceil(props.currentPage / props.defaultPages);
});

// 페이지 목록 생성
const visiblePages = computed(() => {
  const pages = [];

  for (let i = firstPage.value; i <= lastPage.value; i++) {
    pages.push(i);
  }
  return pages;
});

const updatePageQuery = (newPage, newLimit) => {
  store.commit('setPagination', {newPage, newLimit});
};

watch(() => props.currentPage, (newPage) => {
  updatePageQuery(newPage, props.limit);
}, { immediate: false })

// watch(() => props.limit, (value) => {
//   updatePageQuery(props.currentPage, value);
// }, { immediate: false })

// 첫 페이지로 이동
const allPrev = () => {
  const newPage = 1;
  if (newPage >= 1) {
    emit("changePage", newPage);
  }
};

// 이전 페이지로 이동하는 함수 (prev)
const prev = () => {
  if (props.currentPage > 1) {
    emit("changePage", props.currentPage - 1);
  }
};

// 다음 페이지로 이동하는 함수 (next)
const next = () => {
  if (props.currentPage < totalPage.value) {
    emit("changePage", props.currentPage + 1);
  }
};

// 마지막 페이지로 이동
const allNext = () => {
  const newPage = totalPage.value;
  if (newPage <= totalPage.value) {
    emit("changePage", newPage);
  }
};

// 특정 페이지 선택 함수
const selectPage = (page) => {
  if (page !== props.currentPage && page >= 1 && page <= totalPage.value) {
    updatePageQuery(page);
    emit("changePage", page);
  }

};
</script>

<template>
  <section class="paging flex y-center">
    <!-- 이전 페이지 그룹 및 이전 페이지 버튼 -->
    <div class="prev-wrap flex xy-center" :class="{ disabled: currentPage === 1 }">
      <div @click="allPrev">
        <span class="be-icon size-16 icon-grey-md icon-arrow">
          <i class="font-icon-left-double-arrow" />
        </span>
      </div>
      <div @click="prev">
        <span class="be-icon size-16 icon-grey-md icon-arrow">
          <i class="font-icon-left-arrow" />
        </span>
      </div>
    </div>

    <!-- 페이지 번호 리스트 -->
    <ul class="pagingList">
      <template v-for="page in visiblePages" :key="page">
        <li class="be-font size-13 paging-number" :class="{ 'active': page === currentPage, one: totalPage === 1 }" @click="selectPage(page)">
          {{ page }}
        </li>
      </template>
    </ul>

    <!-- 다음 페이지 그룹 및 다음 페이지 버튼 -->
    <div class="next-wrap flex xy-center" :class="{ disabled: currentPage === totalPage }">
      <div @click="next">
        <span class="be-icon size-16 icon-grey-md icon-arrow">
          <i class="font-icon-right-arrow" />
        </span>
      </div>
      <div @click="allNext">
        <span class="be-icon size-16 icon-grey-md icon-arrow">
          <i class="font-icon-right-double-arrow" />
        </span>
      </div>
    </div>

    <!-- 전체 페이지 표시 -->
    <div class="total-page">
      <span class="be-font size-13 text-grey-sm">
        {{ `${currentPage} / ${totalPage}` }}
      </span>
    </div>
  </section>
</template>

<style scoped lang="scss">
.paging {
  gap: 5px;

  .prev-wrap, .next-wrap {
    gap: 5px;

    div {
      display: flex;
      justify-content: center;
      align-items: center;
      width: 32px;
      height: 32px;
      padding: 8px;
      border: 1px solid $line-sm;
      background-color: $whiteColor;
      border-radius: 5px;
      box-sizing: border-box;
      cursor: pointer;
      transition: all .3s;

      &:hover {
        background-color: $hover-grey-bg;
      }
    }
    &.disabled {
      div {
        cursor: initial;
        pointer-events: none;
        .icon-arrow {
          opacity: 0.3;
        }
      }
    }
  }

  .pagingList {
    display: flex;
    justify-content: center;
    align-items: center;
    list-style: none;
    padding: 0;
    border: 1px solid $line-sm;
    border-radius: $radius-4;

    li {
      width: 32px;
      height: 32px;
      cursor: pointer;
      background: $whiteColor;
      text-align: center;
      text-transform: uppercase;
      padding: 8px;
      box-sizing: border-box;
      border-right: 1px solid $line-sm;
      transition: all .3s;

      &:first-child {
        border-radius: 4px 0 0 4px;
      }

      &:last-child {
        border-radius: 0 4px 4px 0;
        border-right: none;
      }

      &:hover:not(.active) {
        background-color: $hover-grey-bg;
      }

      &.active {
        color: #ec0047;
      }

      &.one {
        border-radius: 5px;
      }
    }
  }

  .total-page {
    margin-left: 15px;
  }
}
</style>
