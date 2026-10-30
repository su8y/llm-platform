---
name: "산업군: 레저"
description: "레저 부문(여행, 호텔, 스포츠, 관광)의 JSON-LD 스키마 작성 가이드"
---

# 레저 (Leisure) - JSON-LD 스키마 작성 가이드

## 기본 스키마 타입

### 1. TouristAttraction (관광지)
**필수 필드:**
- name: 명칭
- url: 웹사이트
- address: 주소
- image: 사진

**권장 필드:**
- description: 상세 설명
- telephone: 연락처
- aggregateRating: 방문객 평점
- geo: 위치 (좌표)
- openingHoursSpecification: 운영 시간
- priceRange: 가격대

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "TouristAttraction",
  "name": "서울 N타워",
  "url": "https://example.com/nseoul-tower",
  "image": "https://example.com/tower.jpg",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "남산공원 길 105",
    "addressRegion": "서울",
    "addressCountry": "KR"
  },
  "telephone": "02-1234-5678",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.6",
    "ratingCount": "3500"
  },
  "priceRange": "₩10000-25000"
}
```

### 2. Hotel (호텔/숙박)
**필수 필드:**
- name: 호텔명
- url: 웹사이트
- address: 주소
- image: 이미지

**권장 필드:**
- description: 설명
- telephone: 전화
- aggregateRating: 평점
- priceRange: 가격대
- amenityFeature: 시설
- petsAllowed: 반려동물 동반 가능 여부
- roomCount: 객실 수

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Hotel",
  "name": "럭셔리 호텔",
  "url": "https://luxury-hotel.example.com",
  "image": "https://luxury-hotel.example.com/main.jpg",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "강남로 123",
    "addressRegion": "서울",
    "addressCountry": "KR"
  },
  "telephone": "02-2000-1234",
  "priceRange": "₩200000-500000",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "ratingCount": "2500"
  },
  "amenityFeature": [
    { "@type": "LocationFeatureSpecification", "name": "WiFi" },
    { "@type": "LocationFeatureSpecification", "name": "Swimming Pool" }
  ]
}
```

### 3. SportsActivityLocation (스포츠 시설)
**필수 필드:**
- name: 시설명
- url: 웹사이트
- address: 주소

**권장 필드:**
- image: 사진
- description: 설명
- telephone: 연락처
- openingHoursSpecification: 운영 시간
- priceRange: 이용료

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "SportsActivityLocation",
  "name": "테니스 클럽",
  "url": "https://tennis-club.example.com",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "올림픽대로 100",
    "addressRegion": "서울",
    "addressCountry": "KR"
  },
  "image": "https://tennis-club.example.com/court.jpg",
  "telephone": "02-5000-1234"
}
```

### 4. Event (행사/축제)
**필수 필드:**
- name: 행사명
- startDate: 시작일
- url: 페이지
- location: 장소

**권장 필드:**
- description: 설명
- endDate: 종료일
- image: 이미지
- organizer: 주최자
- performer: 출연자
- ticketUrl: 예매 링크
- price: 입장료

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Event",
  "name": "서울 봄 축제",
  "url": "https://festival.example.com",
  "startDate": "2024-04-01T09:00:00+09:00",
  "endDate": "2024-04-30T18:00:00+09:00",
  "location": {
    "@type": "Place",
    "name": "여의도 공원",
    "address": {
      "@type": "PostalAddress",
      "addressRegion": "서울",
      "addressCountry": "KR"
    }
  },
  "image": "https://festival.example.com/poster.jpg",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.7",
    "ratingCount": "1200"
  }
}
```

### 5. TravelAction (여행 패키지)
**필수 필드:**
- name: 패키지명
- url: 페이지
- description: 설명

**권장 필드:**
- price: 가격
- priceCurrency: 통화
- image: 이미지
- duration: 기간
- itinerary: 일정 상세
- includedService: 포함 서비스

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "TravelAction",
  "name": "유럽 5개국 12일 투어",
  "url": "https://travel.example.com/europe-tour",
  "description": "프랑스, 스위스, 이탈리아 등",
  "price": {
    "@type": "PriceSpecification",
    "price": "2500000",
    "priceCurrency": "KRW"
  },
  "duration": "P12D",
  "image": "https://travel.example.com/europe.jpg"
}
```

## 자주 함께 사용되는 스키마 조합

### 호텔 + 부대시설
```json
{
  "@context": "https://schema.org",
  "@type": "Hotel",
  "name": "호텔명",
  "url": "https://hotel.example.com",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.7",
    "ratingCount": "1500"
  },
  "amenityFeature": [
    { "@type": "LocationFeatureSpecification", "name": "Restaurant" },
    { "@type": "LocationFeatureSpecification", "name": "Spa" },
    { "@type": "LocationFeatureSpecification", "name": "Fitness Center" }
  ]
}
```

### 관광지 + 근처 관광지 (BreadcrumbList 활용)
```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "관광지1", "item": "https://example.com/attraction1" },
    { "@type": "ListItem", "position": 2, "name": "관광지2", "item": "https://example.com/attraction2" }
  ]
}
```

## 레저 관련 중요 필드 정리

| 필드 | 설명 | 예시값 |
|------|------|--------|
| aggregateRating | 평점 | 4.5/5.0 |
| priceRange | 가격대 | ₩10000-50000 |
| openingHoursSpecification | 운영 시간 | Mo-Su 09:00-18:00 |
| image | 고품질 이미지 | 1200x800px 이상 |
| telephone | 예약/문의 전화 | 국가코드 포함 |