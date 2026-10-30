---
name: "산업군: 공공"
description: "공공 부문(공공 서비스, 기관, 사회공헌, 행정 서비스)의 JSON-LD 스키마 작성 가이드"
---

# 공공 (Public) - JSON-LD 스키마 작성 가이드

## 기본 스키마 타입

### 1. Organization (공기관/행정기관)
**필수 필드:**
- name: 기관명
- url: 공식 웹사이트
- address: 주소 (PostalAddress)
- contactPoint: 연락처 (ContactPoint)

**권장 필드:**
- image: 기관 로고
- sameAs: 공식 소셜 미디어, 정부포털
- description: 기관 설명
- foundingDate: 설립일
- areaServed: 서비스 지역

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "서울시청",
  "url": "https://seoul.go.kr",
  "logo": "https://seoul.go.kr/logo.png",
  "address": {
    "@type": "PostalAddress",
    "addressCountry": "KR",
    "addressRegion": "서울",
    "streetAddress": "중로 110"
  },
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "02-120",
    "contactType": "Customer Service",
    "areaServed": "KR"
  },
  "sameAs": [
    "https://www.facebook.com/seoulcity",
    "https://twitter.com/seoul_kr"
  ]
}
```

### 2. LocalBusiness (지역 행정 사무소)
**필수 필드:**
- name: 사무소 명
- address: 주소
- telephone: 연락처

**권장 필드:**
- openingHoursSpecification: 운영 시간
- image: 사무소 사진
- description: 역할 설명

### 3. GovernmentService (공공 서비스)
**필수 필드:**
- name: 서비스명
- url: 서비스 페이지
- serviceType: 서비스 유형
- jurisdiction: 관할지역

**권장 필드:**
- description: 상세 설명
- processingTime: 처리 기간 (ISO 8601)
- fee: 수수료 정보

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "GovernmentService",
  "name": "운전면허 갱신",
  "url": "https://example.gov/license-renewal",
  "serviceType": "License Renewal",
  "jurisdiction": "Seoul",
  "processingTime": "PT3D",
  "fee": {
    "@type": "PriceSpecification",
    "price": "10000",
    "priceCurrency": "KRW"
  }
}
```

### 4. HowTo (신청/절차 안내)
**필수 필드:**
- name: 절차명
- step: 단계별 안내 (HowToStep 배열)

**권장 필드:**
- estimatedDuration: 예상 소요 시간
- image: 절차 이미지
- tool/supply: 필요한 서류/준비물

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "주민등록증 발급 받기",
  "estimatedDuration": "PT30M",
  "step": [
    {
      "@type": "HowToStep",
      "position": 1,
      "name": "방문",
      "text": "주민센터 방문",
      "url": "https://example.gov/visit"
    },
    {
      "@type": "HowToStep",
      "position": 2,
      "name": "신청",
      "text": "신청서 작성 및 제출"
    },
    {
      "@type": "HowToStep",
      "position": 3,
      "name": "발급",
      "text": "주민등록증 수령"
    }
  ]
}
```

## 자주 함께 사용되는 스키마 조합

### 정책 + 공지사항
```json
[
  {
    "@type": "Organization",
    "name": "행정기관명",
    "url": "https://example.gov"
  },
  {
    "@type": "NewsArticle",
    "headline": "새로운 정책 시행",
    "datePublished": "2024-12-01",
    "publisher": {
      "@type": "Organization",
      "name": "행정기관명"
    }
  }
]
```

### 서비스 신청 절차
```json
[
  {
    "@type": "GovernmentService",
    "name": "민원 서비스",
    "url": "https://example.gov/service"
  },
  {
    "@type": "HowTo",
    "name": "신청 절차",
    "associatedWith": {
      "@type": "GovernmentService",
      "name": "민원 서비스"
    }
  }
]
```