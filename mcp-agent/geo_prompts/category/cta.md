---
name: "페이지 유형: CTA 유도 페이지"
description: "CTA 페이지의 JSON-LD 스키마 작성 가이드. BuyAction, RegisterAction, ReservationAction 등"
---

# CTA 유도 페이지 - JSON-LD 스키마 작성 가이드

## 페이지 특성
CTA(Call-To-Action) 페이지는 사용자를 특정 행동(결제, 가입, 공유, 예약 등)으로 유도하는 페이지입니다.\nAI 검색 엔진에 행동 가능성과 구체적인 오퍼 정보를 명확하게 제공해야 합니다.

## 우선 권장 스키마

### 1. BuyAction (구매 유도)
상품 구매를 유도하는 CTA

**필수 포함:**
- target: 구매 페이지 URL
- name: 행동 설명 (예: \"지금 구매\", \"주문하기\")

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "상품명",
  "url": "https://shop.example.com/product-001",
  "potentialAction": {
    "@type": "BuyAction",
    "target": "https://shop.example.com/checkout/product-001",
    "name": "지금 구매하기"
  },
  "offers": {
    "@type": "Offer",
    "price": "99000",
    "priceCurrency": "KRW"
  }
}
```

### 2. RegisterAction (가입 유도)
회원가입, 구독, 신청을 유도하는 CTA

**필수 포함:**
- target: 가입 페이지 URL
- name: \"지금 가입하기\", \"구독하기\" 등

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Service",
  "name": "프리미엄 구독 서비스",
  "url": "https://service.example.com",
  "potentialAction": {
    "@type": "RegisterAction",
    "target": "https://service.example.com/signup",
    "name": "지금 가입하기"
  },
  "offers": {
    "@type": "Offer",
    "price": "9900",
    "priceCurrency": "KRW",
    "billingDuration": "P1M"
  }
}
```

### 3. ReservationAction (예약 유도)
숙박, 식당, 서비스 예약을 유도하는 CTA

**필수 포함:**
- target: 예약 페이지 URL
- name: \"예약하기\", \"예약 신청\"

**권장:**
- priceSpecification: 예약에 필요한 비용

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Hotel",
  "name": "럭셔리 호텔",
  "url": "https://hotel.example.com",
  "potentialAction": {
    "@type": "ReservationAction",
    "target": "https://hotel.example.com/reservation",
    "name": "지금 예약하기"
  },
  "priceRange": "₩150000-300000"
}
```

### 4. ShareAction (공유 유도)
콘텐츠 공유를 유도하는 CTA

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "공유할 가치 있는 기사",
  "url": "https://blog.example.com/article-001",
  "potentialAction": [
    {
      "@type": "ShareAction",
      "target": "https://www.facebook.com/sharer/sharer.php?u=https://blog.example.com/article-001",
      "name": "페이스북에 공유"
    },
    {
      "@type": "ShareAction",
      "target": "https://twitter.com/intent/tweet?url=https://blog.example.com/article-001",
      "name": "트위터에 공유"
    }
  ]
}
```

### 5. SubscribeAction (구독 유도)
뉴스레터, 채널 구독 유도

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "블로그/뉴스사이트",
  "url": "https://blog.example.com",
  "potentialAction": {
    "@type": "SubscribeAction",
    "target": "https://blog.example.com/subscribe",
    "name": "뉴스레터 구독하기"
  }
}
```

## CTA 유형별 스키마 조합

### 상품 구매 CTA + 할인 오퍼
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "상품명",
  "potentialAction": {
    "@type": "BuyAction",
    "target": "https://shop.example.com/checkout"
  },
  "offers": [
    {
      "@type": "Offer",
      "price": "89000",
      "priceCurrency": "KRW",
      "availability": "InStock",
      "description": "정상가"
    },
    {
      "@type": "Offer",
      "price": "69000",
      "priceCurrency": "KRW",
      "availability": "InStock",
      "priceValidUntil": "2024-12-31",
      "description": "한정 할인가 (20% OFF)"
    }
  ]
}
```

### 호텔 예약 CTA + 특가 정보
```json
{
  "@context": "https://schema.org",
  "@type": "Hotel",
  "name": "호텔명",
  "potentialAction": {
    "@type": "ReservationAction",
    "target": "https://hotel.example.com/book"
  },
  "priceRange": "₩150000-250000",
  "offers": {
    "@type": "Offer",
    "priceCurrency": "KRW",
    "price": "120000",
    "priceValidUntil": "2024-12-15",
    "description": "조기 예약 할인"
  }
}
```

### 서비스 구독 CTA
```json
{
  "@context": "https://schema.org",
  "@type": "Service",
  "name": "SaaS 서비스",
  "potentialAction": {
    "@type": "RegisterAction",
    "target": "https://service.example.com/signup"
  },
  "offers": [
    {
      "@type": "Offer",
      "name": "Free Trial",
      "price": "0",
      "billingDuration": "P7D"
    },
    {
      "@type": "Offer",
      "name": "Pro",
      "price": "99",
      "priceCurrency": "USD",
      "billingDuration": "P1M"
    }
  ]
}
```

## CTA 페이지 스키마 작성 체크리스트

### 행동 정의
- [ ] 명확한 CTA 유형 선택 (BuyAction, RegisterAction 등)
- [ ] 정확한 행동 페이지 URL
- [ ] 간결한 CTA 텍스트 (\"지금 구매\", \"무료 가입\" 등)

### 오퍼/제안 정보
- [ ] 명확한 가격 정보
- [ ] 통화 명시
- [ ] 유효 기간 (있는 경우)
- [ ] 할인 또는 특가 정보
- [ ] 제약 조건 또는 조건 (있는 경우)

### 긴급성 강조
- [ ] 제한된 시간 오퍼
- [ ] 제한된 재고 표시
- [ ] 마감 날짜 명시
- [ ] 조기 신청 보너스

### 신뢰도 요소
- [ ] 평점/리뷰 포함
- [ ] 보증/환불 정책
- [ ] 보안 배지/인증
- [ ] 사용자 추천

## CTA 페이지 최적화 팁

1. **명확한 제안**
   - \"지금 구매\", \"한정 할인\" 등 구체적 표현
   - 가격은 한눈에 보이도록
   - 할인율이 있으면 명확히 표시

2. **긴급성 부여**
   - \"오늘만 50% 할인\"
   - \"남은 재고: 5개\"
   - \"2024년 12월 31일까지\"

3. **신뢰도 강화**
   - 사용자 리뷰 (4.5점 이상)
   - \"10,000명 이상 구매\"
   - \"30일 환불 보증\"

4. **이미지 활용**
   - 상품/서비스의 매력적인 이미지
   - 사용 장면 또는 결과 이미지
   - 일관된 브랜딩

5. **여러 CTA 제공**
   - \"지금 구매\" (주요 CTA)
   - \"장바구니 담기\" (보조 CTA)
   - \"더 알아보기\" (정보 CTA)

## 자주 함께 사용되는 조합

### 다중 가격 옵션 CTA
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "상품",
  "potentialAction": {
    "@type": "BuyAction",
    "target": "https://shop.example.com/checkout"
  },
  "offers": [
    {
      "@type": "Offer",
      "name": "기본",
      "price": "10000",
      "priceCurrency": "KRW"
    },
    {
      "@type": "Offer",
      "name": "프리미엄",
      "price": "20000",
      "priceCurrency": "KRW",
      "priceValidUntil": "2024-12-31"
    }
  ]
}
```

### 제한 시간 오퍼
```json
{
  "@context": "https://schema.org",
  "@type": "Offer",
  "name": \"한정 할인\",
  "price": "69000\",
  "priceCurrency": \"KRW\",
  "priceValidUntil": \"2024-12-15T23:59:59+09:00\",
  "availability": \"InStock\",
  \"validFrom\": \"2024-12-01T00:00:00+09:00\"
}
```