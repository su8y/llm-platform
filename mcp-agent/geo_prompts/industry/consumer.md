---
name: "산업군: 소비/생활"
description: "소비/생활 부문(패션, 식음료, 가전, 커머스 등)의 JSON-LD 스키마 작성 가이드"
---

# 소비/생활 (Consumer & Lifestyle) - JSON-LD 스키마 작성 가이드

## 기본 스키마 타입

### 1. Product (상품)
**필수 필드:**
- name: 상품명
- url: 상품 페이지
- image: 상품 이미지
- description: 설명

**권장 필드:**
- brand: 브랜드
- manufacturer: 제조사
- category: 카테고리
- aggregateRating: 평점
- review: 리뷰
- offers: 가격/구매 옵션
- sku: 상품 코드
- color: 색상
- size: 사이즈
- material: 재료

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "프리미엄 슬림 청바지",
  "url": "https://shop.example.com/jeans-slim-001",
  "image": [
    "https://shop.example.com/jeans1.jpg",
    "https://shop.example.com/jeans2.jpg"
  ],
  "description": "편안한 착용감의 슬림핏 청바지",
  "brand": {
    "@type": "Brand",
    "name": "FashionBrand"
  },
  "sku": "JEANS-SLIM-001-BK",
  "color": "Black",
  "size": ["28", "30", "32", "34"],
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.6",
    "ratingCount": "2500"
  },
  "offers": {
    "@type": "Offer",
    "url": "https://shop.example.com/jeans-slim-001",
    "priceCurrency": "KRW",
    "price": "89900",
    "availability": "InStock"
  }
}
```

### 2. AggregateOffer (다양한 옵션/가격)
**필수 필드:**
- priceCurrency: 통화
- lowPrice: 최저가
- highPrice: 최고가
- offerCount: 판매처 수

**권장 필드:**
- offers: 개별 Offer 정보

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "스마트폰 케이스",
  "url": "https://shop.example.com/case-001",
  "aggregateOffer": {
    "@type": "AggregateOffer",
    "priceCurrency": "KRW",
    "lowPrice": "12900",
    "highPrice": "24900",
    "offerCount": "5"
  }
}
```

### 3. FoodEstablishment (음식점)
**필수 필드:**
- name: 음식점명
- url: 웹사이트
- address: 주소
- cuisine: 요리 종류

**권장 필드:**
- telephone: 전화번호
- image: 사진
- aggregateRating: 평점
- review: 리뷰
- menu: 메뉴
- priceRange: 가격대
- openingHoursSpecification: 운영 시간
- acceptsReservations: 예약 가능

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Restaurant",
  "name": "맛있는 한식당",
  "url": "https://restaurant.example.com",
  "image": "https://restaurant.example.com/main.jpg",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "강남로 456",
    "addressRegion": "서울",
    "addressCountry": "KR"
  },
  "telephone": "02-123-4567",
  "cuisine": "Korean",
  "priceRange": "₩15000-40000",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.7",
    "ratingCount": "3200"
  }
}
```

### 4. BeautyBusiness (뷰티 시설)
**필수 필드:**
- name: 시설명
- url: 웹사이트
- address: 주소
- telephone: 전화번호

**권장 필드:**
- image: 사진
- description: 설명
- aggregateRating: 평점
- priceRange: 가격대
- openingHoursSpecification: 운영 시간
- staff: 직원 정보

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "HealthAndBeautyBusiness",
  "name": "프리미엄 뷰티샵",
  "url": "https://beauty.example.com",
  "image": "https://beauty.example.com/salon.jpg",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "강남로 789",
    "addressRegion": "서울",
    "addressCountry": "KR"
  },
  "telephone": "02-987-6543",
  "priceRange": "₩50000-200000",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "ratingCount": "1800"
  }
}
```

### 5. Store (소매점)
**필수 필드:**
- name: 상점명
- url: 웹사이트
- address: 주소
- image: 사진

**권장 필드:**
- telephone: 전화번호
- description: 설명
- aggregateRating: 평점
- priceRange: 가격대
- openingHoursSpecification: 운영 시간

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Store",
  "name": "쇼핑몰",
  "url": "https://mall.example.com",
  "image": "https://mall.example.com/exterior.jpg",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "영동대로 100",
    "addressRegion": "서울",
    "addressCountry": "KR"
  },
  "telephone": "02-555-1234",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.5",
    "ratingCount": "5000"
  }
}
```

## 자주 함께 사용되는 스키마 조합

### 상품 + 상세 정보
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "상품명",
  "url": "https://shop.example.com/product",
  "image": "https://shop.example.com/image.jpg",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.5",
    "ratingCount": "1000"
  },
  "offers": {
    "@type": "Offer",
    "price": "50000",
    "priceCurrency": "KRW",
    "availability": "InStock"
  },
  "review": [
    {
      "@type": "Review",
      "author": { "@type": "Person", "name": "고객1" },
      "reviewRating": { "@type": "Rating", "ratingValue": "5" },
      "reviewBody": "정말 좋아요!"
    }
  ]
}
```

### 음식점 + 메뉴 + 예약
```json
{
  "@context": "https://schema.org",
  "@type": "Restaurant",
  "name": "레스토랑명",
  "url": "https://restaurant.example.com",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.6",
    "ratingCount": "2500"
  },
  "acceptsReservations": "True",
  "menu": "https://restaurant.example.com/menu.pdf"
}
```

## 소비/생활 관련 중요 필드

| 필드 | 설명 | 예시 |
|------|------|------|
| sku | 상품 코드 | PROD-001-BK-S |
| color | 색상 | Black, White |
| size | 사이즈 | S, M, L, XL |
| material | 재료 | Cotton, Polyester |
| availability | 재고 상태 | InStock, OutOfStock |
| priceRange | 가격대 | ₩10000-50000 |
| aggregateRating | 평점 | 4.5/5.0 |

## 전자상거래 스키마 작성 팁
- 높은 품질의 상품 이미지 필수 (최소 200x200px)
- 실제 가격 정보 정확히 기재
- 재고 상태(availability) 명확히 표시
- 고객 리뷰/평점 최대한 포함
- 배송 정보가 있으면 DeliveryChargeSpecification 추가