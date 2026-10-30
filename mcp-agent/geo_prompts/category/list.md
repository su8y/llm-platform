---
name: "페이지 유형: 목록 페이지"
description: "목록 페이지의 JSON-LD 스키마 작성 가이드. CollectionPage, ItemList, SearchResultsPage 활용"
---

# 목록 페이지 - JSON-LD 스키마 작성 가이드

## 페이지 특성
목록 페이지는 여러 아이템(상품, 기사, 서비스 등)을 나열하는 페이지입니다.
검색 엔진이 전체 목록을 이해하고 개별 아이템을 발견할 수 있도록 구조화가 중요합니다.

## 우선 권장 스키마

### 1. CollectionPage (목록/컬렉션 페이지)
**필수 포함:**
- name: 페이지 제목
- url: 페이지 URL
- description: 페이지 설명

**권장:**
- image: 대표 이미지
- mainEntity: 목록의 주요 엔티티
- hasPart: 포함된 아이템들

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  "name": "상품 목록",
  "url": "https://shop.example.com/products",
  "description": "우리의 전체 상품 카테고리",
  "image": "https://shop.example.com/category.jpg"
}
```

### 2. ItemList (항목 목록)
각 아이템의 구조화된 목록

**필수 포함:**
- itemListElement: 개별 아이템 배열
- position: 목록 내 순서

**권장:**
- numberOfItems: 전체 아이템 수
- name: 목록명

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "name": "인기 상품",
  "numberOfItems": "25",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "상품1",
      "url": "https://shop.example.com/product-1",
      "image": "https://shop.example.com/product1.jpg"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "상품2",
      "url": "https://shop.example.com/product-2",
      "image": "https://shop.example.com/product2.jpg"
    }
  ]
}
```

### 3. SearchResultsPage (검색 결과 페이지)
검색 결과를 보여주는 목록 페이지

**필수 포함:**
- query: 검색 쿼리
- mainEntity: 검색 결과 (ItemList)

**권장:**
- numberOfResults: 결과 수
- image: 결과 섬네일

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "SearchResultsPage",
  "name": "검색 결과: 청바지",
  "url": "https://shop.example.com/search?q=청바지",
  "mainEntity": {
    "@type": "ItemList",
    "numberOfItems": "45",
    "itemListElement": [
      {
        "@type": "ListItem",
        "position": 1,
        "name": "프리미엄 청바지",
        "url": "https://shop.example.com/jeans-001",
        "image": "https://shop.example.com/jeans1.jpg"
      }
    ]
  }
}
```

## 목록 유형별 스키마 조합

### 상품 목록
```json
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "name": "카테고리명 상품",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "item": {
        "@type": "Product",
        "name": "상품명",
        "image": "image.jpg",
        "offers": {
          "@type": "Offer",
          "price": "50000",
          "priceCurrency": "KRW"
        }
      }
    }
  ]
}
```

### 기사/뉴스 목록
```json
{
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  "name": "뉴스",
  "url": "https://news.example.com",
  "mainEntity": {
    "@type": "ItemList",
    "itemListElement": [
      {
        "@type": "ListItem",
        "position": 1,
        "item": {
          "@type": "NewsArticle",
          "headline": "뉴스 제목",
          "datePublished": "2024-11-01",
          "image": "image.jpg",
          "url": "https://news.example.com/article-1"
        }
      }
    ]
  }
}
```

### 서비스/시설 목록
```json
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "name": "서비스 목록",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "item": {
        "@type": "Service",
        "name": "서비스명",
        "description": "설명",
        "provider": {
          "@type": "Organization",
          "name": "회사명"
        }
      }
    }
  ]
}
```

## 목록 페이지 스키마 작성 체크리스트

### 페이지 메타정보
- [ ] 명확한 페이지 제목
- [ ] 완전한 페이지 URL
- [ ] 상세한 설명 (100-160자)
- [ ] 대표 이미지 (1200x630px)

### 아이템 구조
- [ ] 모든 아이템에 position 번호 지정
- [ ] 각 아이템의 이름/제목
- [ ] 각 아이템의 고유 URL
- [ ] 각 아이템의 이미지 (최소 200x200px)

### 가격/평점 정보 (상품인 경우)
- [ ] 정확한 가격
- [ ] 통화 정보 (priceCurrency)
- [ ] 재고 상태 (availability)
- [ ] 평점 (있는 경우)

### 날짜 정보 (뉴스/기사인 경우)
- [ ] 발행일 (datePublished)
- [ ] 수정일 (dateModified)
- [ ] 저자 정보

## 목록 페이지 최적화 팁

1. **페이지네이션 처리**
   - 첫 페이지에 ItemList 포함
   - 각 페이지의 URL이 고유하고 정확해야 함
   - 다음 페이지 링크 명시

2. **아이템 수량**
   - numberOfItems: 해당 페이지의 아이템 수 정확히
   - 너무 많은 아이템은 여러 페이지로 분산

3. **정렬 순서**
   - position이 실제 표시 순서와 일치
   - 인기도, 최신순, 가격순 등 정렬 방식 고려

4. **이미지 최적화**
   - 각 아이템별 고품질 이미지 (최소 300x300px)
   - 일관된 비율 유지 (정사각형 권장)

5. **필터링/카테고리**
   - 필터 옵션이 있으면 각각 다른 페이지로 제공
   - BreadcrumbList로 현재 위치 표시

## 자주 함께 사용되는 조합

### 페이지 + 브레드크럼
```json
[
  {
    "@type": "BreadcrumbList",
    "itemListElement": [
      { "@type": "ListItem", "position": 1, "name": "홈", "item": "https://example.com" },
      { "@type": "ListItem", "position": 2, "name": "카테고리", "item": "https://example.com/category" },
      { "@type": "ListItem", "position": 3, "name": "목록", "item": "https://example.com/list" }
    ]
  },
  {
    "@type": "CollectionPage",
    "name": "목록",
    "url": "https://example.com/list",
    "mainEntity": {
      "@type": "ItemList",
      "itemListElement": [...]
    }
  }
]
```

### 목록 + 페이지네이션
```json
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "name": "상품 목록",
  "numberOfItems": "100",
  "itemListElement": [...],
  "url": "https://shop.example.com/products?page=1",
  "nextPage": "https://shop.example.com/products?page=2"
}
```