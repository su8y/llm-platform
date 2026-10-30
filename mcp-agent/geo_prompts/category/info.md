---
name: "페이지 유형: 정보 확인 페이지"
description: "정보 확인 페이지의 JSON-LD 스키마 작성 가이드. Order, Invoice, Reservation, Subscription"
---

# 정보 확인 페이지 - JSON-LD 스키마 작성 가이드

## 페이지 특성
정보 확인 페이지는 사용자의 개인 정보, 주문 내역, 계정 정보 등을 표시하는 페이지입니다.
AI 검색 엔진에 트랜잭션 정보, 상태, 타임스탠프를 명확하게 제공해야 합니다.

## 우선 권장 스키마

### 1. Order (주문 정보)
사용자의 주문 내역을 표시

**필수 포함:**
- orderNumber: 주문번호
- orderDate: 주문일
- orderStatus: 주문 상태
- customer: 고객 정보
- orderItem: 주문 상품 목록
- totalPrice: 총액
- priceCurrency: 통화

**권장:**
- url: 주문 상세 페이지 URL
- broker: 판매처
- trackingNumber: 배송 추적 번호

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Order",
  "orderNumber": "ORD-20241115-12345",
  "url": "https://shop.example.com/order/ORD-20241115-12345",
  "orderDate": "2024-11-15T10:30:00+09:00",
  "orderStatus": "http://schema.org/OrderProcessing",
  "customer": {
    "@type": "Person",
    "name": "김고객"
  },
  "orderItem": [
    {
      "@type": "OrderItem",
      "orderItemNumber": "1",
      "orderedItem": {
        "@type": "Product",
        "name": "상품명",
        "sku": "PROD-001",
        "image": "https://shop.example.com/product.jpg"
      },
      "orderItemStatus": "http://schema.org/OrderDelivered",
      "orderQuantity": "1",
      "unitPriceSpecification": {
        "@type": "PriceSpecification",
        "price": "50000",
        "priceCurrency": "KRW"
      }
    }
  ],
  "totalPrice": {
    "@type": "PriceSpecification",
    "price": "53000",
    "priceCurrency": "KRW",
    "description": "상품 50,000 + 배송료 3,000"
  }
}
```

### 2. Invoice (청구서)
사용자의 청구 정보

**필수 포함:**
- invoiceNumber: 청구서 번호
- invoiceDate: 청구일
- customer: 고객 정보
- totalPrice: 총액

**권장:**
- paymentStatus: 결제 상태
- paymentMethod: 결제 방법
- url: 청구서 상세 페이지

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Invoice",
  "invoiceNumber": "INV-2024-11-001",
  "url": "https://service.example.com/invoice/INV-2024-11-001",
  "invoiceDate": "2024-11-15",
  "paymentStatus": "PaymentComplete",
  "paymentMethod": "CreditCard",
  "customer": {
    "@type": "Person",
    "name": "이고객",
    "email": "customer@example.com"
  },
  "totalPrice": {
    "@type": "PriceSpecification",
    "price": "99000",
    "priceCurrency": "KRW"
  }
}
```

### 3. Reservation (예약 정보)
호텔, 레스토랑, 서비스 예약 정보

**필수 포함:**
- reservationId: 예약 번호
- reservationStatus: 예약 상태
- reservationFor: 예약 대상 (호텔, 레스토랑 등)
- underName: 예약자명
- reservationDate: 예약일
- checkinDate/checkoutDate: 체크인/아웃 날짜

**권장:**
- url: 예약 상세 페이지
- totalPrice: 총 가격
- partySize: 인원 수

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Reservation",
  "reservationId": "RES-2024-111501",
  "url": "https://hotel.example.com/reservation/RES-2024-111501",
  "reservationStatus": "http://schema.org/ReservationConfirmed",
  "reservationDate": "2024-11-15T14:00:00+09:00",
  "reservationFor": {
    "@type": "Hotel",
    "name": "럭셔리 호텔"
  },
  "underName": {
    "@type": "Person",
    "name": "박예약"
  },
  "checkinDate": "2024-12-01",
  "checkoutDate": "2024-12-03",
  "partySize": "2",
  "totalPrice": {
    "@type": "PriceSpecification",
    "price": "450000",
    "priceCurrency": "KRW",
    "description": "2박 (225,000/박)"
  }
}
```

### 4. Subscription (구독 정보)
구독 서비스의 계정 정보

**필수 포함:**
- name: 구독명
- orderDate: 구독 시작일
- potentialAction: 취소, 변경 등의 가능한 액션
- price: 구독료
- billingDuration: 청구 주기

**권장:**
- url: 구독 관리 페이지
- inLanguage: 언어
- description: 구독 설명

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Order",
  "name": "프리미엄 구독",
  "url": "https://service.example.com/subscription",
  "orderDate": "2024-11-01",
  "orderStatus": "http://schema.org/OrderInProcess",
  "customer": {
    "@type": "Person",
    "name": "최구독"
  },
  "totalPrice": {
    "@type": "PriceSpecification",
    "price": "9900",
    "priceCurrency": "KRW",
    "billingDuration": "P1M",
    "description": "매월 9,900원"
  }
}
```

## 정보 확인 유형별 스키마

### 배송 추적 정보
```json
{
  "@context": "https://schema.org",
  "@type": "Order",
  "orderNumber": "ORD-123456",
  "orderStatus": "http://schema.org/OrderShipped",
  "orderItem": [
    {
      "@type": "OrderItem",
      "orderItemStatus": "http://schema.org/OrderDelivered",
      "orderedItem": {
        "@type": "Product",
        "name": "상품명"
      }
    }
  ],
  "potentialAction": {
    "@type": "TrackAction",
    "target": "https://tracking.example.com/ORD-123456"
  }
}
```

### 다중 아이템 주문
```json
{
  "@context": "https://schema.org",
  "@type": "Order",
  "orderNumber": "ORD-789",
  "orderItem": [
    {
      "@type": "OrderItem",
      "orderedItem": { "@type": "Product", "name": "상품1" },
      "orderQuantity": "2"
    },
    {
      "@type": "OrderItem",
      "orderedItem": { "@type": "Product", "name": "상품2" },
      "orderQuantity": "1"
    }
  ],
  "totalPrice": {
    "@type": "PriceSpecification",
    "price": "150000",
    "priceCurrency": "KRW"
  }
}
```

### 구독 + 결제 예정
```json
{
  "@context": "https://schema.org",
  "@type": "Order",
  "name": "구독 서비스\",
  \"orderStatus\": \"http://schema.org/OrderInProcess\",
  \"totalPrice\": {
    \"@type\": \"PriceSpecification\",
    \"price\": \"99\",
    \"priceCurrency\": \"USD\",
    \"billingDuration\": \"P1M\"
  },
  \"potentialAction\": [
    {
      \"@type\": \"UpdateAction\",
      \"target\": \"https://service.example.com/subscription/change\",
      \"name\": \"플랜 변경\"
    },
    {
      \"@type\": \"DeleteAction\",
      \"target\": \"https://service.example.com/subscription/cancel\",
      \"name\": \"구독 취소\"
    }
  ]
}
```

## 정보 확인 페이지 스키마 작성 체크리스트

### 기본 정보
- [ ] 고유한 주문/청구서/예약 번호
- [ ] 정확한 날짜 정보 (ISO 8601 형식)
- [ ] 고객/사용자 정보 정확성
- [ ] 현재 상태 정보 명시

### 항목 상세
- [ ] 각 주문 항목의 상품명
- [ ] 수량 또는 기간 정보
- [ ] 개별 가격
- [ ] 항목별 상태 (배송 중, 완료 등)

### 금액 정보
- [ ] 상품가 합계
- [ ] 배송료, 세금 등 추가 비용
- [ ] 총액
- [ ] 통화 명시
- [ ] 결제 방법

### 상태 추적
- [ ] 주문 상태 (Pending, Processing, Shipped, Delivered 등)
- [ ] 배송 추적 번호 (있는 경우)
- [ ] 예상 도착 날짜 (배송인 경우)
- [ ] 상태 변경 타임라인

### 추가 정보
- [ ] 고객 지원 연락처
- [ ] 반품/교환 정책 링크
- [ ] 송장 링크 (배송인 경우)
- [ ] 인보이스 다운로드 (결제인 경우)

## 정보 확인 페이지 최적화 팁

1. **상태 명확성**
   - \"배송 중\", \"배송 완료\" 등 명확한 상태 표시
   - 타임라인으로 진행 상황 시각화
   - 다음 예상 이벤트 표시

2. **금액 투명성**
   - 각 비용 항목 명확히 분리
   - 할인 또는 쿠폰 적용액 표시
   - 총액 하이라이트

3. **실시간 업데이트**
   - 배송 추적 정보 실시간 갱신
   - 상태 변경 시 알림 제공
   - 예상 도착 날짜 정확히

4. **접근성**
   - 모든 정보를 쉽게 찾을 수 있도록 배치
   - 중요한 정보는 상단에 위치
   - 인쇄 및 다운로드 기능 제공

5. **사용자 지원**
   - \"어떤 다음 단계인가요?\" FAQ
   - \"반품하려면\" 링크
   - \"더 도움이 필요하신가요?\" 연락처

## 자주 함께 사용되는 조합

### 주문 정보 + 배송 추적
```json
{
  \"@context\": \"https://schema.org\",
  \"@type\": \"Order\",
  \"orderNumber\": \"ORD-123\",
  \"orderStatus\": \"http://schema.org/OrderShipped\",
  \"orderItem\": [...],
  \"trackingNumber\": \"1Z9999999999\",
  \"potentialAction\": {
    \"@type\": \"TrackAction\",
    \"target\": \"https://tracking.example.com/track/1Z9999999999\"
  }
}
```

### 구독 정보 + 액션
```json
{
  \"@context\": \"https://schema.org\",
  \"@type\": \"Order\",
  \"name\": \"Premium Subscription\",
  \"totalPrice\": { \"@type\": \"PriceSpecification\", \"price\": \"99\", \"billingDuration\": \"P1M\" },
  \"potentialAction\": [
    { \"@type\": \"UpdateAction\", \"name\": \"플랜 변경\", \"target\": \"https://...change\" },
    { \"@type\": \"DeleteAction\", \"name\": \"구독 취소\", \"target\": \"https://...cancel\" }
  ]
}
```

## Order Status 표준 값
- http://schema.org/OrderPending (주문 대기)
- http://schema.org/OrderProcessing (처리 중)
- http://schema.org/OrderInTransit (배송 중)
- http://schema.org/OrderDelivered (배송 완료)
- http://schema.org/OrderPickupAvailable (픽업 가능)
- http://schema.org/OrderCancelled (주문 취소)