export const clickOutside = {
  beforeMount(el, binding) {
    el.clickOutsideEvent = (event) => {
      // 엘리먼트 외부에서 클릭된 경우만 실행
      if (!(el === event.target || el.contains(event.target))) {
        binding.value(event); // 전달된 함수 호출
      }
    };
    document.addEventListener('click', el.clickOutsideEvent);
  },
  unmounted(el) {
    document.removeEventListener('click', el.clickOutsideEvent);
  },
};
