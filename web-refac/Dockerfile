FROM node:18.20 as build
WORKDIR /app

# pnpm 설치
# pnpm 메이저 고정: 11+는 Node 18 미지원, 10부터 의존성 build script는 package.json의 pnpm.onlyBuiltDependencies로 허용
RUN npm install -g pnpm@10

ADD . .
# pnpm으로 의존성 설치
RUN pnpm install
# 빌드 시 메모리 증가
RUN NODE_OPTIONS="--max-old-space-size=4096" pnpm run build

FROM node:18.20 as stage
WORKDIR /app

# pnpm 설치
# pnpm 메이저 고정: 11+는 Node 18 미지원, 10부터 의존성 build script는 package.json의 pnpm.onlyBuiltDependencies로 허용
RUN npm install -g pnpm@10

COPY --from=build /app/dist /app/dist
COPY --from=build /app/package.json /app/package.json
COPY --from=build /app/pnpm-lock.yaml* /app/

# pnpm으로 production 의존성만 설치
RUN pnpm install --prod
RUN npm install -g serve

CMD ["serve", "-s", "dist", "-l", "3333"]