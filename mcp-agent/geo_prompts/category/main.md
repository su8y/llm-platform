---
name: "페이지 유형: 메인/브랜딩 페이지"
description: "메인/브랜딩 페이지의 JSON-LD 스키마 작성 가이드. 조직의 신뢰성과 브랜드 정체성 표현"
---

# 메인/브랜딩 페이지 - JSON-LD 스키마 작성 가이드

## 페이지 특성
메인 페이지는 브랜드 및 조직의 정체성을 보여주는 페이지입니다.
AI 검색 엔진에서 조직/브랜드의 신뢰성과 정당성을 강조해야 합니다.

## 우선 권장 스키마

### 1. Organization (조직/회사)
**필수 포함:**
- name: 조직명
- url: 공식 웹사이트
- logo: 로고 이미지
- description: 조직 설명
- contactPoint: 연락처
- address: 주소

**추가 권장:**
- sameAs: 소셜 미디어 링크
- founder: 설립자
- foundingDate: 설립일
- numberOfEmployees: 직원 수
- image: 조직 사진/브랜드 이미지
- areaServed: 서비스 지역

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "회사명",
  "url": "https://example.com",
  "logo": "https://example.com/logo.png",
  "image": "https://example.com/brand-image.jpg",
  "description": "회사 미션 및 비전 설명",
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+82-2-1234-5678",
    "contactType": "Customer Service",
    "areaServed": "KR"
  },
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "강남로 100",
    "addressRegion": "서울",
    "postalCode": "06000",
    "addressCountry": "KR"
  },
  "sameAs": [
    "https://www.facebook.com/company",
    "https://twitter.com/company",
    "https://www.linkedin.com/company/company"
  ],
  "foundingDate": "2010-01-15",
  "numberOfEmployees": 500
}
```

### 2. LocalBusiness (지역 기반 사업)
메인 페이지가 지역 기반 사업(음식점, 상점 등)인 경우 사용

**필수 포함:**
- name: 사업명
- url: 웹사이트
- address: 주소
- image: 외부/내부 사진
- telephone: 전화
- openingHoursSpecification: 운영 시간

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "맛있는 식당",
  "url": "https://restaurant.example.com",
  "image": "https://restaurant.example.com/main.jpg",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "강남로 200",
    "addressRegion": "서울",
    "addressCountry": "KR"
  },
  "telephone": "02-123-4567",
  "openingHoursSpecification": {
    "@type": "OpeningHoursSpecification",
    "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
    "opens": "11:00",
    "closes": "22:00"
  }
}
```

### 3. WebSite (웹사이트 전체)
메인 페이지에서 전체 웹사이트의 기본 정보를 제공

**필수 포함:**
- name: 사이트명
- url: 사이트 URL
- description: 사이트 설명

**권장:**
- image: 대표 이미지
- publisher: 발행자
- potentialAction: SearchAction (검색 기능이 있는 경우)

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "서비스 이름",
  "url": "https://example.com",
  "description": "서비스 설명",
  "image": "https://example.com/og-image.jpg",
  "publisher": {
    "@type": "Organization",
    "name": "발행사",
    "logo": "https://example.com/logo.png"
  },
  "potentialAction": {
    "@type": "SearchAction",
    "target": {
      "@type": "EntryPoint",
      "urlTemplate": "https://example.com/search?q={search_term_string}"
    },
    "query-input": "required name=search_term_string"
  }
}
```

## 메인 페이지 스키마 작성 체크리스트

### 조직 정보
- [ ] 명확한 조직명 (법인명과 일치)
- [ ] 공식 로고 (고품질 이미지)
- [ ] 상세한 조직 설명
- [ ] 정확한 연락처 정보
- [ ] 모든 사무소/지점 주소
- [ ] 설립일 및 회사 규모

### 소셜 미디어
- [ ] 모든 공식 소셜 미디어 계정 링크
- [ ] 정확한 프로필 URL
- [ ] 팔로워 수 또는 활동성 표시

### 신뢰성 요소
- [ ] 인증/자격증 정보 (있는 경우)
- [ ] 수상 이력
- [ ] 파트너십 정보
- [ ] 미디어 언급

### 이미지 최적화
- [ ] 로고: 1200x630px 이상, PNG/SVG 권장
- [ ] 조직 사진: 최소 1200x800px
- [ ] OG 이미지: 1200x630px

## 메인 페이지 최적화 팁

1. **신뢰도 강화**
   - 회사 규모(직원 수, 설립년도) 명시
   - 정확한 연락처 여러 개 제공
   - 실제 주소 및 운영 시간 정확히

2. **브랜드 일관성**
   - Organization 스키마의 name과 웹사이트 제목 일치
   - 모든 이미지에서 일관된 브랜드 아이덴티티

3. **지역 최적화**
   - areaServed에 서비스 제공 지역 명시
   - 다중 지점이 있으면 각각의 LocalBusiness 추가

4. **검색 최적화**
   - SearchAction을 추가하여 사이트 검색 기능 명시
   - 주요 키워드를 description에 포함

## 자주 함께 사용되는 조합

### Organization + SearchAction
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "회사명",
  "url": "https://example.com",
  "potentialAction": {
    "@type": "SearchAction",
    "target": {
      "@type": "EntryPoint",
      "urlTemplate": "https://example.com/search?q={search_term}"
    }
  }
}
```

### Organization + 다중 지점
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "회사명",
  "@id": "https://example.com",
  "url": "https://example.com",
  "branch": [
    {
      "@type": "LocalBusiness",
      "name": "서울 지점",
      "address": { "@type": "PostalAddress", "addressRegion": "Seoul" }
    },
    {
      "@type": "LocalBusiness",
      "name": "부산 지점",
      "address": { "@type": "PostalAddress", "addressRegion": "Busan" }
    }
  ]
}
```