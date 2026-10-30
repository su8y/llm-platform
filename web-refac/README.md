# LLM Platform Web (web-refac)

Vue 3 + Vite 프론트엔드. 전체 설치 절차는 상위 [INSTALL.md](../INSTALL.md)를 참고하세요.

## 개발 서버

```bash
cp .env.example .env   # VITE_APP_API_URL, VITE_APP_NAME, VITE_SUPPORT_EMAIL
pnpm install
pnpm run dev
```

## 빌드 / 배포

`VITE_*` 값은 빌드 시 번들에 박히므로 바꾸면 다시 빌드합니다.

```bash
pnpm run build                     # dist/
docker compose build web && docker compose up -d web   # 저장소 루트에서
```

## 구조

```
src/
├── views/        # 라우트 단위 화면 (Playground, FileDrive, Reference, Email, Admin, History …)
├── components/   # 공통 컴포넌트 (Header, SideMenu, Modal, Editor, Chart …)
├── api/          # 백엔드 라우터 prefix 단위 axios 함수 (res.data 만 반환)
├── libs/         # http-client(인터셉터), auth-helper(토큰 저장), constants, utils
├── store/        # Vuex
├── router/       # vue-router (미로그인 시 /signin 으로)
├── composables/  # 재사용 로직
├── styles/       # SCSS
└── data/         # i18n 메시지
```

- 인증 토큰은 localStorage(`app-auth`)에 두고, 401 응답이면 refresh token 으로 재발급 후 1회 재시도합니다.
- 컴포넌트에서 axios 를 직접 import 하지 않고 `api/*.js` 를 통해 호출합니다.
