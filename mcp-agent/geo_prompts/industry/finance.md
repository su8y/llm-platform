---
name: "산업군: 금융"
description: "금융 부문(금융 서비스, 보험, 은행, 자산 관리, 증권, 카드)의 JSON-LD 스키마 작성 가이드"
---

# 금융 (Finance) - JSON-LD 스키마 작성 가이드

## 기본 스키마 타입

### 1. FinancialService (금융 서비스)
**필수 필드:**
- name: 서비스명
- url: 서비스 페이지
- areaServed: 서비스 지역

**권장 필드:**
- description: 서비스 설명
- image: 로고/대표 이미지
- telephone: 고객 서비스 전화
- contactPoint: 연락처
- founder: 설립사
- serviceType: 서비스 유형

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "FinancialService",
  "name": "신용카드 서비스",
  "url": "https://bank.example.com/credit-card",
  "description": "고객맞춤형 신용카드 서비스",
  "areaServed": "KR",
  "serviceType": "Credit Card",
  "provider": {
    "@type": "Organization",
    "name": "은행명"
  }
}
```

### 2. BankAccount (계좌)
**필수 필드:**
- name: 계좌명
- accountId: 계좌 유형
- accountCurrency: 통화

**권장 필드:**
- description: 계좌 설명
- interestRate: 이율
- minimumDeposit: 최소 예치금
- provider: 은행 정보

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "BankAccount",
  "name": "고금리 정기예금",
  "accountId": "savings_premium",
  "accountCurrency": "KRW",
  "interestRate": {
    "@type": "PriceSpecification",
    "price": "3.5",
    "priceCurrency": "percent"
  },
  "minimumDeposit": {
    "@type": "PriceSpecification",
    "price": "1000000",
    "priceCurrency": "KRW"
  }
}
```

### 3. FinancialProduct (금융 상품)
**필수 필드:**
- name: 상품명
- url: 상품 페이지
- provider: 제공사

**권장 필드:**
- description: 상품 설명
- image: 상품 이미지
- productionDate: 출시일
- price: 수수료/가격
- interestRate: 이율
- duration: 상품 기간
- aggregateRating: 평점

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "FinancialProduct",
  "name": "변액보험 플러스",
  "url": "https://insurance.example.com/variable-insurance",
  "description": "펀드 연계 보험 상품",
  "provider": {
    "@type": "Organization",
    "name": "보험사명"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.3",
    "ratingCount": "850"
  }
}
```

### 4. InvestmentOrFund (펀드/투자상품)
**필수 필드:**
- name: 펀드명
- url: 펀드 페이지
- fundType: 펀드 유형 (주식, 채권, 혼합 등)

**권장 필드:**
- description: 펀드 설명
- fundManager: 펀드 매니저
- fundExpense: 운용 비용
- rating: 평점
- netAssetValue: 순자산

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "InvestmentOrFund",
  "name": "글로벌 주식 펀드",
  "url": "https://fund.example.com/global-stock",
  "fundType": "Equity Fund",
  "fundManager": {
    "@type": "Person",
    "name": "펀드 매니저명"
  },
  "fundExpense": "0.85%"
}
```

### 5. MoneyTransfer (송금/이체)
**필수 필드:**
- name: 서비스명
- url: 서비스 페이지

**권장 필드:**
- description: 서비스 설명
- price: 수수료
- processingTime: 처리 시간
- supportedCountry: 지원 국가

## 자주 함께 사용되는 스키마 조합

### 금융사 + 다양한 상품
```json
[
  {
    "@type": "Organization",
    "name": "금융사명",
    "url": "https://example.com"
  },
  {
    "@type": "FinancialProduct",
    "name": "상품1",
    "provider": { "@type": "Organization", "name": "금융사명" }
  },
  {
    "@type": "FinancialProduct",
    "name": "상품2",
    "provider": { "@type": "Organization", "name": "금융사명" }
  }
]
```

### 상품 + 가격 + 평점
```json
{
  "@context": "https://schema.org",
  "@type": "FinancialProduct",
  "name": "상품명",
  "url": "https://example.com/product",
  "price": {
    "@type": "PriceSpecification",
    "priceCurrency": "KRW",
    "price": "0"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.5",
    "ratingCount": "2000"
  }
}
```

## 금융 상품 관련 권장 Meta Tags
- og:type: website
- article:published_time (상품 출시일)
- article:modified_time (업데이트일)
- robots: index, follow