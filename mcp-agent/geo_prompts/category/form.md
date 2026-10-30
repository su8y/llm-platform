---
name: "페이지 유형: 사용자입력 페이지"
description: "사용자입력 페이지의 JSON-LD 스키마 작성 가이드. HowTo, BreadcrumbList, AggregateOffer 활용"
---

# 사용자입력 페이지 - JSON-LD 스키마 작성 가이드

## 페이지 특성\n사용자입력 페이지는 결제, 주문, 상품가입, 예약 등의 정보를 입력받는 페이지입니다.\nAI 검색 엔진에 프로세스 진행 상황, 필수 정보, 보안 정보를 명확하게 제공해야 합니다.

## 우선 권장 스키마

### 1. HowTo (단계별 입력 프로세스)
구매, 가입, 예약 등의 다단계 프로세스를 설명

**필수 포함:**
- name: 프로세스명
- step: 단계별 설명
- estimatedDuration: 예상 소요 시간

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "온라인 상품 주문 및 결제",
  "estimatedDuration": "PT5M",
  "step": [
    {
      "@type": "HowToStep",
      "position": 1,
      "name": "배송지 입력",
      "text": "주소와 연락처 정보 입력",
      "url": "https://shop.example.com/checkout/step1"
    },
    {
      "@type": "HowToStep",
      "position": 2,
      "name": "배송 방법 선택",
      "text": "배송 방법 선택 (일반 배송, 특급 배송)",
      "url": "https://shop.example.com/checkout/step2"
    },
    {
      "@type": "HowToStep",
      "position": 3,
      "name": "결제 정보 입력",
      "text": "신용카드 또는 계좌이체 정보 입력",
      "url": "https://shop.example.com/checkout/step3"
    },
    {
      "@type": "HowToStep",
      "position": 4,
      "name": "주문 확인",
      "text": "최종 확인 후 주문 완료",
      "url": "https://shop.example.com/checkout/confirmation"
    }
  ]
}
```

### 2. BreadcrumbList (프로세스 진행 표시)
현재 어느 단계인지 표시

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "장바구니", "item": "https://shop.example.com/cart" },
    { "@type": "ListItem", "position": 2, "name": \"배송정보\", \"item\": \"https://shop.example.com/checkout/shipping\" },
    { \"@type\": \"ListItem\", \"position\": 3, \"name\": \"결제\", \"item\": \"https://shop.example.com/checkout/payment\", \"isCurrentPage\": true },
    { \"@type\": \"ListItem\", \"position\": 4, \"name\": \"완료\", \"item\": \"https://shop.example.com/checkout/confirmation\" }
  ]
}
```

### 3. AggregateOffer (입력 단계별 가격 옵션)
각 단계에서 선택 가능한 옵션(배송료, 추가 서비스 등)

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "AggregateOffer",
  "name": "배송 옵션",
  "priceCurrency": "KRW",
  "lowPrice": "0",
  "highPrice": "5000",
  "offerCount": "3",
  "offers": [
    {
      "@type": "Offer",
      "name": "일반 배송",
      "price": "0",
      "priceCurrency": "KRW",
      "description": "3-5 영업일"
    },
    {
      "@type": "Offer",
      "name": "당일 배송",
      "price": "3000",
      "priceCurrency": "KRW",
      "description": "오늘 배송\"
    },
    {
      "@type": "Offer",
      "name": "특급 배송\",
      \"price\": \"5000\",
      \"priceCurrency\": \"KRW\",
      \"description\": \"2시간 배송\"
    }
  ]
}
```

### 4. CreativeWork (이용약관/개인정보)
입력 시 동의해야 할 약관 정보

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "CreativeWork",
  "name": "이용약관\",
  \"url\": \"https://example.com/terms\",
  \"datePublished\": \"2024-01-01\",
  \"dateModified\": \"2024-11-15\",
  \"author\": {
    \"@type\": \"Organization\",
    \"name\": \"회사명\"
  }
}
```

## 입력 페이지 유형별 스키마

### 결제/주문 입력
```json
{
  \"@context\": \"https://schema.org\",
  \"@type\": \"HowTo\",
  \"name\": \"온라인 구매 프로세스\",
  \"estimatedDuration\": \"PT5M\",
  \"step\": [
    {
      \"@type\": \"HowToStep\",
      \"position\": 1,
      \"name\": \"배송지 입력\",
      \"text\": \"주소 검색, 상세주소 입력\",
      \"url\": \"https://checkout.example.com/step1\"
    },
    {
      \"@type\": \"HowToStep\",
      \"position\": 2,
      \"name\": \"배송방법 선택\",
      \"text\": \"배송료 확인 후 선택\",
      \"url\": \"https://checkout.example.com/step2\"
    },
    {
      \"@type\": \"HowToStep\",
      \"position\": 3,
      \"name\": \"결제 정보 입력\",
      \"text\": \"신용카드, 계좌이체, 전자지갑 선택\",
      \"url\": \"https://checkout.example.com/step3\"
    },
    {
      \"@type\": \"HowToStep\",
      \"position\": 4,
      \"name\": \"최종 확인\",
      \"text\": \"주문 내용 확인 및 주문 완료\",
      \"url\": \"https://checkout.example.com/confirmation\"
    }
  ]
}
```

### 상품 가입/구독 입력
```json
{
  \"@context\": \"https://schema.org\",
  \"@type\": \"HowTo\",
  \"name\": \"구독 가입 프로세스\",
  \"estimatedDuration\": \"PT3M\",
  \"step\": [
    {
      \"@type\": \"HowToStep\",
      \"position\": 1,
      \"name\": \"플랜 선택\",
      \"text\": \"Basic, Pro, Enterprise 중 선택\",
      \"url\": \"https://subscribe.example.com/plans\"
    },
    {
      \"@type\": \"HowToStep\",
      \"position\": 2,
      \"name\": \"개인정보 입력\",
      \"text\": \"이메일, 비밀번호 설정\",
      \"url\": \"https://subscribe.example.com/signup\"
    },
    {
      \"@type\": \"HowToStep\",
      \"position\": 3,
      \"name\": \"결제정보 입력\",
      \"text\": \"신용카드 정보 입력\",
      \"url\": \"https://subscribe.example.com/billing\"
    },
    {
      \"@type\": \"HowToStep\",
      \"position\": 4,
      \"name\": \"가입 완료\",
      \"text\": \"이메일 확인 및 서비스 이용 시작\",
      \"url\": \"https://subscribe.example.com/welcome\"
    }
  ]
}
```

### 예약 입력
```json
{
  \"@context\": \"https://schema.org\",
  \"@type\": \"HowTo\",
  \"name\": \"호텔 예약 프로세스\",
  \"estimatedDuration\": \"PT5M\",
  \"step\": [
    {
      \"@type\": \"HowToStep\",
      \"position\": 1,
      \"name\": \"날짜 선택\",
      \"text\": \"체크인/체크아웃 날짜 선택\",
      \"url\": \"https://hotel.example.com/search\"
    },
    {
      \"@type\": \"HowToStep\",
      \"position\": 2,
      \"name\": \"객실 선택\",
      \"text\": \"원하는 객실 유형 선택\",
      \"url\": \"https://hotel.example.com/rooms\"
    },
    {
      \"@type\": \"HowToStep\",
      \"position\": 3,
      \"name\": \"고객정보 입력\",
      \"text\": \"이름, 전화, 이메일 입력\",
      \"url\": \"https://hotel.example.com/guest-info\"
    },
    {
      \"@type\": \"HowToStep\",
      \"position\": 4,
      \"name\": \"결제\",
      \"text\": \"결제 방법 선택 후 결제\",
      \"url\": \"https://hotel.example.com/payment\"
    },
    {
      \"@type\": \"HowToStep\",
      \"position\": 5,
      \"name\": \"예약 확인\",
      \"text\": \"확인 메일 수신 및 예약번호 확인\",
      \"url\": \"https://hotel.example.com/confirmation\"
    }
  ]
}
```

## 입력 페이지 스키마 작성 체크리스트

### 프로세스 정의
- [ ] 명확한 프로세스명
- [ ] 각 단계별 설명 (명확하고 간결)
- [ ] 예상 소요 시간 (ISO 8601 형식)
- [ ] 각 단계별 URL

### 진행 표시
- [ ] BreadcrumbList로 현재 단계 표시
- [ ] 이전/다음 단계 네비게이션
- [ ] 완료된 단계와 남은 단계 구분

### 선택 옵션
- [ ] 각 단계에서 선택 가능한 옵션 명시
- [ ] 옵션별 가격 또는 조건
- [ ] 추천 또는 인기 옵션 표시

### 보안/신뢰
- [ ] 개인정보 보호 정책 링크
- [ ] SSL/보안 배지 표시
- [ ] 약관 및 동의 링크

## 입력 페이지 최적화 팁

1. **명확한 단계 표시**
   - \"1/4 단계\", \"2/4 단계\" 등 진행도 표시
   - 완료된 단계는 체크마크 표시
   - 현재 단계는 하이라이트

2. **짧은 소요 시간**
   - 3-5 단계 권장
   - 전체 소요 시간을 명시하면 사용자가 계획할 수 있음
   - 너무 길면 사용자 이탈 증가

3. **명확한 옵션 표시**
   - 각 옵션의 가격/조건 명시
   - 기본 옵션 또는 추천 옵션 표시
   - 선택에 따른 금액 변화 실시간 표시

4. **신뢰도 강화**
   - 보안 배지 표시
   - \"100만 명 이상이 이용했습니다\"
   - \"즉시 사용 시작 가능\"

5. **입력 유효성 검사**
   - 필수 필드 명확히 표시
   - 실시간 입력 검증 메시지
   - 오류 발생 시 구체적인 해결책 제시

## 자주 함께 사용되는 조합

### 다단계 프로세스 + 진행도
```json
[
  {
    \"@type\": \"BreadcrumbList\",
    \"itemListElement\": [
      { \"@type\": \"ListItem\", \"position\": 1, \"name\": \"배송정보\", \"item\": \"...\" },
      { \"@type\": \"ListItem\", \"position\": 2, \"name\": \"결제\", \"item\": \"...\", \"isCurrentPage\": true },
      { \"@type\": \"ListItem\", \"position\": 3, \"name\": \"완료\", \"item\": \"...\" }
    ]
  },
  {
    \"@type\": \"HowTo\",
    \"name\": \"결제 프로세스\",
    \"step\": [...]
  }
]
```

### 옵션 선택 + 가격
```json
{
  \"@context\": \"https://schema.org\",
  \"@type\": \"AggregateOffer\",
  \"name\": \"배송 옵션\",
  \"priceCurrency\": \"KRW\",
  \"lowPrice\": \"0\",
  \"highPrice\": \"5000\",
  \"offers\": [...]
}
```