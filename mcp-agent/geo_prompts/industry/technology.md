---
name: "산업군: 기술"
description: "기술 부문(건축, 제조, 반도체, 에너지, 우주항공 등)의 JSON-LD 스키마 작성 가이드"
---

# 기술 (Technology) - JSON-LD 스키마 작성 가이드

## 기본 스키마 타입

### 1. Product (기술 제품)
**필수 필드:**
- name: 제품명
- url: 제품 페이지
- description: 설명
- image: 제품 이미지

**권장 필드:**
- manufacturer: 제조사
- brand: 브랜드
- releaseDate: 출시일
- aggregateRating: 평점
- review: 리뷰
- offers: 가격 정보
- specifications: 사양

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "스마트 센서 모듈",
  "url": "https://tech.example.com/sensor-v3",
  "description": "IoT용 고정밀 센서",
  "image": "https://tech.example.com/sensor.jpg",
  "manufacturer": {
    "@type": "Organization",
    "name": "기술 회사명"
  },
  "brand": {
    "@type": "Brand",
    "name": "TechBrand"
  },
  "releaseDate": "2024-01-15",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.7",
    "ratingCount": "1250"
  }
}
```

### 2. SoftwareApplication (소프트웨어)
**필수 필드:**
- name: 애플리케이션명
- url: 앱 페이지
- description: 설명

**권장 필드:**
- image: 스크린샷/로고
- applicationCategory: 카테고리
- operatingSystem: 지원 OS
- requiresSubscription: 구독 필요 여부
- softwareVersion: 버전
- fileSize: 파일 크기
- downloadUrl: 다운로드 링크
- aggregateRating: 평점

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "AI 분석 도구",
  "url": "https://software.example.com/ai-analyzer",
  "description": "데이터 분석을 위한 AI 기반 소프트웨어",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": ["Windows", "macOS", "Linux"],
  "softwareVersion": "3.2.1",
  "downloadUrl": "https://software.example.com/download/analyzer",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.6",
    "ratingCount": "2100"
  },
  "offers": {
    "@type": "Offer",
    "price": "99.99",
    "priceCurrency": "USD"
  }
}
```

### 3. CreativeWork (기술 문서/논문)
**필수 필드:**
- name: 제목
- url: 페이지
- author: 저자
- datePublished: 발행일

**권장 필드:**
- description: 요약
- image: 썸네일
- keywords: 키워드
- inLanguage: 언어
- articleBody: 본문 요약

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "ScholarlyArticle",
  "name": "AI 신경망 최적화 연구",
  "url": "https://research.example.com/paper-123",
  "author": {
    "@type": "Person",
    "name": "김연구원"
  },
  "datePublished": "2024-06-01",
  "description": "대규모 신경망 최적화 기법 연구",
  "keywords": "AI, Neural Network, Optimization"
}
```

### 4. BreadcrumbList (기술 카테고리 네비게이션)
**필수 필드:**
- itemListElement: 항목 리스트

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "반도체", "item": "https://tech.example.com/semiconductor" },
    { "@type": "ListItem", "position": 2, "name": "공정 기술", "item": "https://tech.example.com/process" },
    { "@type": "ListItem", "position": 3, "name": "5nm 공정", "item": "https://tech.example.com/5nm" }
  ]
}
```

### 5. Event (기술 컨퍼런스/전시)
**필수 필드:**
- name: 이벤트명
- startDate: 시작일
- url: 페이지
- location: 장소

**권장 필드:**
- description: 설명
- endDate: 종료일
- image: 이미지
- organizer: 주최자
- performer: 발표자
- doorTime: 입장 시간

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Event",
  "name": "기술 컨퍼런스 2024",
  "url": "https://tech-conf.example.com",
  "startDate": "2024-10-15T09:00:00+09:00",
  "endDate": "2024-10-17T18:00:00+09:00",
  "location": {
    "@type": "Place",
    "name": "컨벤션센터",
    "address": {
      "@type": "PostalAddress",
      "addressCountry": "KR"
    }
  },
  "image": "https://tech-conf.example.com/poster.jpg"
}
```

## 자주 함께 사용되는 스키마 조합

### 제조사 + 제품 + 평점
```json
[
  {
    "@type": "Organization",
    "name": "기술 회사",
    "url": "https://techco.example.com"
  },
  {
    "@type": "Product",
    "name": "제품명",
    "manufacturer": { "@type": "Organization", "name": "기술 회사" },
    "aggregateRating": {
      "@type": "AggregateRating",
      "ratingValue": "4.5",
      "ratingCount": "1000"
    }
  }
]
```

### 소프트웨어 + 플랫폼 지원
```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "크로스플랫폼 도구",
  "url": "https://software.example.com/tool",
  "operatingSystem": ["Windows", "macOS", "Linux", "iOS", "Android"],
  "applicationCategory": "DeveloperApplication"
}
```

## 기술 업계 관련 중요 필드

| 필드 | 설명 | 예시 |
|------|------|------|
| softwareVersion | 소프트웨어 버전 | 3.2.1 |
| operatingSystem | 지원 OS | Windows, macOS |
| systemRequirements | 시스템 요구사항 | RAM 8GB, HDD 2GB |
| releaseDate | 출시일 | 2024-01-15 |
| fileSize | 파일 크기 | 250MB |
| applicationCategory | 앱 카테고리 | BusinessApplication |

## 기술 제품 스키마 작성 팁
- 정확한 사양 정보 포함
- 최신 업데이트 날짜 명시
- 시스템 요구사항 명확히 기재
- 지원되는 플랫폼/환경 모두 나열
- 평가 및 리뷰 정보 포함