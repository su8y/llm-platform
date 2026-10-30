---
name: "산업군: IT"
description: "IT 부문(통신 서비스, IT 솔루션)의 JSON-LD 스키마 작성 가이드"
---

# IT (Information Technology) - JSON-LD 스키마 작성 가이드

## 기본 스키마 타입

### 1. ITService (IT 서비스)
**필수 필드:**
- name: 서비스명
- url: 서비스 페이지
- description: 설명
- serviceType: 서비스 유형

**권장 필드:**
- provider: 제공사
- image: 로고/대표 이미지
- telephone: 고객 서비스 전화
- areaServed: 서비스 지역
- aggregateRating: 평점

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Service",
  "name": "클라우드 호스팅 서비스",
  "url": "https://cloud.example.com/hosting",
  "description": "확장 가능한 클라우드 기반 호스팅",
  "serviceType": "Cloud Hosting",
  "provider": {
    "@type": "Organization",
    "name": "IT 서비스 회사"
  },
  "areaServed": ["KR", "US", "JP"],
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.7",
    "ratingCount": "2500"
  }
}
```

### 2. SoftwareApplication (통신 솔루션/앱)
**필수 필드:**
- name: 애플리케이션명
- url: 앱 페이지
- description: 설명
- applicationCategory: 카테고리

**권장 필드:**
- image: 스크린샷/로고
- operatingSystem: 지원 OS
- softwareVersion: 버전
- downloadUrl: 다운로드 링크
- price: 가격
- priceCurrency: 통화
- aggregateRating: 평점
- permissions: 필요 권한

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "비즈니스 커뮤니케이션 앱",
  "url": "https://app.example.com/biz-comm",
  "description": "엔터프라이즈급 통신 솔루션",
  "image": "https://app.example.com/screenshot.jpg",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": ["iOS", "Android", "Windows", "macOS"],
  "downloadUrl": "https://app.example.com/download",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.6",
    "ratingCount": "5000"
  },
  "offers": {
    "@type": "Offer",
    "price": "99.99",
    "priceCurrency": "USD",
    "availability": "InStock"
  }
}
```

### 3. Product (IT 제품/솔루션)
**필수 필드:**
- name: 제품명
- url: 제품 페이지
- image: 제품 이미지
- description: 설명

**권장 필드:**
- manufacturer: 제조사
- brand: 브랜드
- releaseDate: 출시일
- aggregateRating: 평점
- specifications: 사양
- offers: 가격 정보

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "API 관리 플랫폼",
  "url": "https://products.example.com/api-management",
  "image": "https://products.example.com/api-platform.jpg",
  "description": "엔터프라이즈급 API 관리 및 모니터링",
  "manufacturer": {
    "@type": "Organization",
    "name": "IT 솔루션 회사"
  },
  "releaseDate": "2024-03-01",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "ratingCount": "1800"
  }
}
```

### 4. BreadcrumbList (IT 제품 분류)
**필수 필드:**
- itemListElement: 카테고리 항목

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "IT 솔루션", "item": "https://example.com/solutions" },
    { "@type": "ListItem", "position": 2, "name": "클라우드 서비스", "item": "https://example.com/cloud" },
    { "@type": "ListItem", "position": 3, "name": "데이터베이스", "item": "https://example.com/database" }
  ]
}
```

### 5. OnlineCourse (IT 교육/기술 훈련)
**필수 필드:**
- name: 강좌명
- url: 강좌 페이지
- description: 설명
- provider: 제공 기관

**권장 필드:**
- instructor: 강사
- image: 강좌 이미지
- duration: 기간
- learningResourceType: 학습 자료 유형
- aggregateRating: 평점
- price: 강좌 가격

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "OnlineCourse",
  "name": "클라우드 아키텍처 마스터",
  "url": "https://learn.example.com/cloud-architecture",
  "description": "AWS, Azure, GCP 클라우드 아키텍처 교육",
  "image": "https://learn.example.com/course-banner.jpg",
  "provider": {
    "@type": "Organization",
    "name": "IT 교육 플랫폼"
  },
  "instructor": {
    "@type": "Person",
    "name": "클라우드 전문가"
  },
  "duration": "P6W",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "ratingCount": "3200"
  }
}
```

### 6. Offer (IT 제품 가격/라이선스)
**필수 필드:**
- name: 플랜명 (예: Standard, Professional)
- priceCurrency: 통화
- price: 가격

**권장 필드:**
- description: 플랜 설명
- url: 구매 페이지
- availability: 구매 가능 여부
- pricingDetails: 상세 가격 정보

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "SaaS 소프트웨어",
  "url": "https://saas.example.com",
  "offers": [
    {
      "@type": "Offer",
      "name": "Starter Plan",
      "price": "29.99",
      "priceCurrency": "USD",
      "description": "소규모 팀용",
      "availability": "InStock"
    },
    {
      "@type": "Offer",
      "name": "Professional Plan",
      "price": "99.99",
      "priceCurrency": "USD",
      "description": "중규모 조직용",
      "availability": "InStock"
    },
    {
      "@type": "Offer",
      "name": "Enterprise Plan",
      "price": "Custom",
      "priceCurrency": "USD",
      "description": "대규모 조직용 맞춤형",
      "availability": "InStock"
    }
  ]
}
```

## 자주 함께 사용되는 스키마 조합

### SaaS + 가격 플랜
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "협업 도구",
  "url": "https://saas.example.com",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.7",
    "ratingCount": "5000"
  },
  "offers": [
    {
      "@type": "Offer",
      "name": "Free",
      "price": "0",
      "priceCurrency": "USD"
    },
    {
      "@type": "Offer",
      "name": "Pro",
      "price": "49.99",
      "priceCurrency": "USD"
    }
  ]
}
```

### IT 교육 + 강사 + 평점
```json
{
  "@context": "https://schema.org",
  "@type": "OnlineCourse",
  "name": "강좌명",
  "url": "https://learn.example.com/course",
  "instructor": {
    "@type": "Person",
    "name": "강사명"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "ratingCount": "2000"
  }
}
```

### IT 서비스 + 지원 영역
```json
{
  "@context": "https://schema.org",
  "@type": "Service",
  "name": "서비스명",
  "url": "https://service.example.com",
  "areaServed": ["Korea", "Asia-Pacific", "North America"],
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.6",
    "ratingCount": "1500"
  }
}
```

## IT 산업 관련 중요 필드

| 필드 | 설명 | 예시 |
|------|------|------|
| applicationCategory | 앱 카테고리 | BusinessApplication, DeveloperApplication |
| operatingSystem | 지원 OS | Windows, macOS, Linux, iOS, Android |
| softwareVersion | 소프트웨어 버전 | 3.2.1 |
| systemRequirements | 시스템 요구사항 | RAM 8GB, SSD 500GB |
| offers | 가격 플랜 | Free, Pro, Enterprise |
| areaServed | 서비스 지역 | 국가 또는 지역 |

## IT 제품/서비스 스키마 작성 팁
1. **버전 정보**: 최신 버전 명시 및 정기적 업데이트
2. **호환성**: 지원하는 모든 OS/플랫폼 나열
3. **가격**: 모든 가격 플랜(Free, Pro, Enterprise) 포함
4. **평점**: 사용자 평점 및 리뷰 최대한 포함
5. **스크린샷**: 소프트웨어는 주요 기능 스크린샷 포함
6. **기술 문서**: 기술 사양 명확하게 기재
7. **지원**: 고객 지원 채널 및 SLA 정보 포함