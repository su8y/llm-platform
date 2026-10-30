---
name: "산업군: 엔터"
description: "엔터 부문(영화, 게임, 음악, 공연, 예술)의 JSON-LD 스키마 작성 가이드"
---

# 엔터 (Entertainment) - JSON-LD 스키마 작성 가이드

## 기본 스키마 타입

### 1. Movie (영화)
**필수 필드:**
- name: 영화제목
- url: 영화 페이지
- image: 포스터 이미지
- datePublished: 개봉일

**권장 필드:**
- description: 줄거리
- director: 감독
- actor: 배우
- genre: 장르
- duration: 상영 시간
- aggregateRating: 평점
- review: 리뷰
- contentRating: 등급

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Movie",
  "name": "영화제목",
  "url": "https://movie.example.com/film-001",
  "image": "https://movie.example.com/poster.jpg",
  "description": "흥미진진한 스토리",
  "datePublished": "2024-07-15",
  "duration": "PT120M",
  "genre": ["Action", "Drama"],
  "contentRating": "PG-13",
  "director": {
    "@type": "Person",
    "name": "감독명"
  },
  "actor": [
    { "@type": "Person", "name": "배우1" },
    { "@type": "Person", "name": "배우2" }
  ],
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "8.2",
    "ratingCount": "5000"
  }
}
```

### 2. Game (게임)
**필수 필드:**
- name: 게임명
- url: 게임 페이지
- image: 게임 이미지

**권장 필드:**
- description: 게임 설명
- genre: 장르
- applicationCategory: 카테고리
- author: 개발사
- datePublished: 출시일
- platformUrl: 플랫폼별 링크
- aggregateRating: 평점

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "VideoGame",
  "name": "액션 게임",
  "url": "https://game.example.com/action-game",
  "image": "https://game.example.com/cover.jpg",
  "description": "스릴있는 액션 게임",
  "genre": ["Action", "Adventure"],
  "author": {
    "@type": "Organization",
    "name": "게임 개발사"
  },
  "datePublished": "2024-05-20",
  "gamePlatform": ["PC", "PlayStation", "Xbox"],
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "8.7",
    "ratingCount": "10000"
  }
}
```

### 3. PerformingArtsTheater (공연)
**필수 필드:**
- name: 공연명
- url: 공연 페이지
- startDate: 시작일
- location: 공연장

**권장 필드:**
- description: 공연 설명
- endDate: 종료일
- image: 공연 이미지
- performer: 출연자
- aggregateRating: 평점
- offers: 티켓 정보

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "TheaterEvent",
  "name": "뮤지컬 공연",
  "url": "https://theater.example.com/musical-001",
  "startDate": "2024-08-01T19:30:00+09:00",
  "endDate": "2024-09-30T19:30:00+09:00",
  "image": "https://theater.example.com/poster.jpg",
  "description": "감동적인 뮤지컬",
  "location": {
    "@type": "Place",
    "name": "공연장",
    "address": {
      "@type": "PostalAddress",
      "addressCountry": "KR"
    }
  },
  "performer": [
    { "@type": "Person", "name": "배우1" }
  ],
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "ratingCount": "3000"
  }
}
```

### 4. MusicPlaylist (음악 플레이리스트)
**필수 필드:**
- name: 플레이리스트명
- url: 페이지
- track: 곡 목록

**권장 필드:**
- description: 설명
- image: 커버 이미지
- creator: 제작자
- datePublished: 발행일
- duration: 총 길이

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "MusicPlaylist",
  "name": "최신 K-POP 히트곡",
  "url": "https://music.example.com/playlist-001",
  "image": "https://music.example.com/cover.jpg",
  "description": "2024년 인기 K-POP 곡들",
  "creator": {
    "@type": "Organization",
    "name": "음악 스트리밍 서비스"
  },
  "track": [
    {
      "@type": "MusicRecording",
      "name": "곡제목1",
      "byArtist": { "@type": "MusicGroup", "name": "아티스트1" }
    },
    {
      "@type": "MusicRecording",
      "name": "곡제목2",
      "byArtist": { "@type": "MusicGroup", "name": "아티스트2" }
    }
  ]
}
```

### 5. CreativeWork (디지털 콘텐츠)
**필수 필드:**
- name: 콘텐츠명
- url: 페이지
- author: 제작자
- datePublished: 발행일

**권장 필드:**
- description: 설명
- image: 썸네일
- contentUrl: 콘텐츠 URL
- keywords: 키워드
- aggregateRating: 평점

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "name": "게임 리뷰: 최신 AAA 게임",
  "url": "https://blog.example.com/game-review-001",
  "image": "https://blog.example.com/review-image.jpg",
  "datePublished": "2024-06-15",
  "author": {
    "@type": "Person",
    "name": "게임 리뷰어"
  },
  "description": "최신 AAA 게임의 상세 리뷰",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.5",
    "ratingCount": "2000"
  }
}
```

## 자주 함께 사용되는 스키마 조합

### 영화 + 리뷰 + 평점
```json
{
  "@context": "https://schema.org",
  "@type": "Movie",
  "name": "영화명",
  "url": "https://movie.example.com/film",
  "image": "https://movie.example.com/poster.jpg",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "8.5",
    "ratingCount": "10000",
    "bestRating": "10",
    "worstRating": "1"
  },
  "review": [
    {
      "@type": "Review",
      "author": { "@type": "Person", "name": "리뷰어" },
      "reviewRating": { "@type": "Rating", "ratingValue": "9" },
      "reviewBody": "훌륭한 영화입니다"
    }
  ]
}
```

### 게임 + 플랫폼 + 평점
```json
{
  "@context": "https://schema.org",
  "@type": "VideoGame",
  "name": "게임명",
  "url": "https://game.example.com/game",
  "gamePlatform": ["PC", "PlayStation 5", "Xbox Series X"],
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "8.8",
    "ratingCount": "50000"
  }
}
```

### 공연 + 출연자 + 티켓
```json
{
  "@context": "https://schema.org",
  "@type": "TheaterEvent",
  "name": "공연명",
  "url": "https://theater.example.com/event",
  "startDate": "2024-08-01T19:30:00+09:00",
  "performer": [
    { "@type": "Person", "name": "주연배우" }
  ],
  "offers": {
    "@type": "Offer",
    "url": "https://theater.example.com/tickets",
    "priceCurrency": "KRW",
    "price": "80000",
    "availability": "InStock"
  }
}
```

## 엔터테인먼트 관련 중요 필드

| 필드 | 설명 | 예시 |
|------|------|------|
| datePublished | 발행/개봉일 | 2024-06-15 |
| duration | 상영/재생 시간 | PT120M (2시간) |
| genre | 장르 | Action, Comedy, Drama |
| aggregateRating | 평점 | 8.5/10 |
| contentRating | 관람 등급 | PG-13, R |
| actor/director | 출연진/감독 | Person 타입 |

## 엔터테인먼트 콘텐츠 스키마 작성 팁
- 고화질 포스터/커버 이미지 필수 (최소 300x450px)
- 정확한 장르 분류 (다중 선택 가능)
- 출연자/제작진 정보 명확히 기재
- 평점은 가능한 한 정확하고 최신으로 유지
- 리뷰 포함 시 출처 명시