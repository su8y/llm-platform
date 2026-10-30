---
name: "페이지 유형: 정보 상세 안내 페이지"
description: "상세 페이지의 JSON-LD 스키마 작성 가이드. Product, Article, Service 등 단일 아이템 정보"
---

# 정보 상세 안내 페이지 - JSON-LD 스키마 작성 가이드

## 페이지 특성
상세 정보 페이지는 단일 아이템(상품, 서비스, 기사, 숙소 등)의 완전한 정보를 제공합니다.
AI 검색 엔진이 세밀한 정보를 이해할 수 있도록 모든 상세 정보를 구조화해야 합니다.

## 우선 권장 스키마

### 1. Product (상품 상세)
**필수 포함:**
- name: 상품명
- image: 상품 이미지 (여러 개)
- description: 상세 설명
- offers: 가격/구매 옵션
- aggregateRating: 평점 (있는 경우)

**권장:**
- sku: 상품 코드
- brand: 브랜드
- color: 색상 옵션
- size: 사이즈 옵션
- material: 재료
- review: 고객 리뷰
- availability: 재고 상태

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "프리미엄 스마트폰",
  "sku": "PHONE-2024-001-BK",
  "brand": {
    "@type": "Brand",
    "name": "TechBrand"
  },
  "image": [
    "https://shop.example.com/phone-1.jpg",
    "https://shop.example.com/phone-2.jpg",
    "https://shop.example.com/phone-3.jpg"
  ],
  "description": "최신 기술이 집약된 프리미엄 스마트폰. 고성능 프로세서, 뛰어난 카메라, 긴 배터리 수명",
  "color": ["Black", "White", "Silver"],
  "offers": {
    "@type": "Offer",
    "url": "https://shop.example.com/phone-001",
    "priceCurrency": "KRW",
    "price": "1299000",
    "availability": "InStock",
    "seller": {
      "@type": "Organization",
      "name": "온라인 쇼핑몰"
    }
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.7",
    "ratingCount": "5000",
    "bestRating": "5",
    "worstRating": "1"
  }
}
```

### 2. Article (기사/콘텐츠)
블로그, 뉴스, 가이드 등 기사 형식의 상세 정보

**필수 포함:**
- headline: 제목
- datePublished: 발행일
- author: 저자
- image: 메인 이미지
- articleBody: 본문 내용

**권장:**
- dateModified: 수정일
- publisher: 발행처
- description: 요약
- wordCount: 글자 수
- aggregateRating: 평점

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "최신 기술 트렌드 분석",
  "url": "https://blog.example.com/tech-trends-2024",
  "image": "https://blog.example.com/article-image.jpg",
  "datePublished": "2024-11-01T09:00:00+09:00",
  "dateModified": "2024-11-15T14:30:00+09:00",
  "author": {
    "@type": "Person",
    "name": "기자명"
  },
  "publisher": {
    "@type": "Organization",
    "name": "블로그/매체명"
  },
  "description": "2024년 최신 기술 트렌드에 대한 심층 분석",
  "articleBody": "기사의 전체 내용...",
  "wordCount": 2500
}
```

### 3. Service (서비스 상세)
특정 서비스에 대한 상세 정보

**필수 포함:**
- name: 서비스명
- description: 상세 설명
- provider: 제공사
- url: 서비스 페이지
- image: 대표 이미지

**권장:**
- serviceType: 서비스 유형
- areaServed: 서비스 지역
- priceRange: 가격대
- aggregateRating: 평점

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Service",
  "name": "클라우드 호스팅 서비스",
  "url": "https://hosting.example.com/service-detail",
  "image": "https://hosting.example.com/service.jpg",
  "description": "엔터프라이즈급 클라우드 호스팅 서비스. 99.99% 가용성, 24/7 지원, 자동 백업 제공",
  "provider": {
    "@type": "Organization",
    "name": "IT 호스팅 회사"
  },
  "serviceType": "Cloud Hosting",
  "priceRange": "₩50000-500000",
  "areaServed": ["Korea", "Asia"]
}
```

### 4. FAQPage (자주 묻는 질문)
상세 페이지에서 FAQ 섹션이 있는 경우

**필수 포함:**
- mainEntity: 질문-답변 배열

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "배송 기간은 얼마나 되나요?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "일반적으로 3-5 영업일 소요됩니다"
      }
    },
    {
      "@type": "Question",
      "name": "반품은 가능한가요?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "구매 후 30일 이내 반품 가능합니다"
      }
    }
  ]
}
```

## 상세 페이지 유형별 스키마

### 호텔/숙박 상세
```json
{
  "@context": "https://schema.org",
  "@type": "Hotel",
  "name": "호텔명",
  "url": "https://hotel.example.com/room-detail",
  "image": ["room1.jpg", "room2.jpg"],
  "description": "럭셔리 더블룸. 킹사이즈 침대, 욕실, 위성 TV, WiFi 무료",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "ratingCount": "2500"
  },
  "amenityFeature": [
    { "@type": "LocationFeatureSpecification", "name": "WiFi" },
    { "@type": "LocationFeatureSpecification", "name": "Air Conditioning" }
  ]
}
```

### 의료/진료 상세
```json
{
  "@context": "https://schema.org",
  "@type": "MedicalBusiness",
  "name": "의료기관",
  "url": "https://medical.example.com/service",
  "description": "심장질환 전문 진료. 최신 진단 장비, 경험 많은 의료진",
  "medicalSpecialty": ["Cardiology"],
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.7",
    "ratingCount": "1200"
  }
}
```

### 부동산 매물 상세
```json
{
  "@context": "https://schema.org",
  "@type": "Residence",
  "name": "강남 아파트 3LDK",
  "url": "https://realestate.example.com/property-123",
  "image": ["apt1.jpg", "apt2.jpg", "apt3.jpg"],
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "강남로 456",
    "addressRegion": "Seoul",
    "addressCountry": "KR"
  },
  "numberOfRooms": "3",
  "floorSize": {
    "@type": "QuantitativeValue",
    "value": "120",
    "unitCode": "MTK"
  },
  "price": {
    "@type": "PriceSpecification",
    "price": "850000000",
    "priceCurrency": "KRW"
  }
}
```

## 상세 페이지 스키마 작성 체크리스트

### 기본 정보
- [ ] 명확한 제목/상품명
- [ ] 완전한 설명 (300자 이상)
- [ ] 다양한 각도의 고품질 이미지 (최소 3개)
- [ ] 주요 사양/특징 명시

### 가격/구매 정보
- [ ] 정확한 가격
- [ ] 통화 명시
- [ ] 재고 상태
- [ ] 배송비 정보 (있는 경우)

### 평가 정보
- [ ] 종합 평점
- [ ] 리뷰 수
- [ ] 개별 리뷰 (3-5개 샘플)

### 저자/출처 정보
- [ ] 저자명
- [ ] 발행일
- [ ] 수정일 (최신 콘텐츠인 경우)
- [ ] 발행처

### 추가 정보
- [ ] FAQ 섹션 (있는 경우)
- [ ] 스펙/사양 상세
- [ ] 관련 상품/서비스 링크

## 상세 페이지 최적화 팁

1. **이미지 최적화**
   - 첫 번째 이미지가 가장 대표적인 이미지
   - 최소 1200x900px, 최대 3000x3000px
   - 여러 각도/상황의 이미지 포함

2. **텍스트 최적화**
   - 제목은 50-60자
   - 설명은 최소 150-200자
   - 주요 키워드 자연스럽게 포함

3. **구조화된 정보**
   - 사양은 테이블 형식 제공
   - 단계별 안내는 HowTo 스키마 사용
   - FAQ는 FAQPage로 구조화

4. **리뷰/평점**
   - 종합 평점과 함께 개별 리뷰 포함
   - 리뷰 수가 많을수록 신뢰도 증가
   - 최근 리뷰 우선 표시

5. **연관 콘텐츠**
   - "관련 상품", "함께 본 상품" 링크
   - BreadcrumbList로 네비게이션 표시