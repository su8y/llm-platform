---
name: "산업군: 정보"
description: "정보 부문(도서, 법률, 부동산, 취업, 커뮤니티)의 JSON-LD 스키마 작성 가이드"
---

# 정보 (Information) - JSON-LD 스키마 작성 가이드

## 기본 스키마 타입

### 1. Book (도서)
**필수 필드:**
- name: 책 제목
- url: 도서 페이지
- author: 저자
- image: 표지 이미지
- datePublished: 발행일

**권장 필드:**
- description: 책 설명
- isbn: ISBN 코드
- inLanguage: 언어
- publisher: 출판사
- numberOfPages: 쪽수
- genre: 장르
- aggregateRating: 평점

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Book",
  "name": "기술 서적 제목",
  "url": "https://bookstore.example.com/book-001",
  "author": {
    "@type": "Person",
    "name": "저자명"
  },
  "image": "https://bookstore.example.com/cover.jpg",
  "datePublished": "2024-01-15",
  "isbn": "978-1234567890",
  "publisher": {
    "@type": "Organization",
    "name": "출판사명"
  },
  "numberOfPages": "320",
  "description": "흥미로운 기술 서적",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.7",
    "ratingCount": "1200"
  }
}
```

### 2. LegalDocument (법률 문서)
**필수 필드:**
- name: 문서명
- url: 문서 페이지
- description: 설명

**권장 필드:**
- datePublished: 발행일
- author: 작성자/기관
- legislationJurisdiction: 관할권
- legislationDate: 법령 발효일

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "LegalDocument",
  "name": "개인정보보호정책",
  "url": "https://example.com/privacy-policy",
  "description": "웹사이트 개인정보 취급 방침",
  "datePublished": "2024-01-01",
  "author": {
    "@type": "Organization",
    "name": "회사명"
  }
}
```

### 3. RealEstateAgent (부동산 중개)
**필수 필드:**
- name: 중개소명
- url: 웹사이트
- address: 주소
- telephone: 전화번호

**권장 필드:**
- image: 사진
- description: 설명
- aggregateRating: 평점
- areaServed: 서비스 지역

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "RealEstateAgent",
  "name": "부동산 중개소",
  "url": "https://realestate.example.com",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "강남로 999",
    "addressRegion": "서울",
    "addressCountry": "KR"
  },
  "telephone": "02-1111-2222",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.6",
    "ratingCount": "850"
  }
}
```

### 4. Residence (부동산 매물)
**필수 필드:**
- name: 물건명
- url: 매물 페이지
- address: 주소
- image: 사진

**권장 필드:**
- description: 설명
- numberOfRooms: 방 개수
- floorSize: 면적
- price: 가격
- priceCurrency: 통화
- agents: 중개인

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Residence",
  "name": "강남 아파트 2LDK",
  "url": "https://realestate.example.com/property-001",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "강남로 456",
    "addressRegion": "서울",
    "postalCode": "06000",
    "addressCountry": "KR"
  },
  "image": [
    "https://realestate.example.com/photo1.jpg",
    "https://realestate.example.com/photo2.jpg"
  ],
  "description": "고급 아파트 매물",
  "numberOfRooms": "2",
  "floorSize": {
    "@type": "QuantitativeValue",
    "value": "84",
    "unitCode": "MTK"
  },
  "price": {
    "@type": "PriceSpecification",
    "price": "600000000",
    "priceCurrency": "KRW",
    "priceType": "SalePrice"
  }
}
```

### 5. JobPosting (구직정보)
**필수 필드:**
- title: 직무명
- description: 직무 설명
- hiringOrganization: 채용 기관
- jobLocation: 근무지

**권장 필드:**
- url: 채용공고 페이지
- baseSalary: 급여
- employmentType: 고용 형태
- datePosted: 등록일
- validThrough: 마감일
- qualifications: 자격조건
- responsibilities: 주요 업무

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "JobPosting",
  "title": "시니어 소프트웨어 엔지니어",
  "url": "https://careers.example.com/job-001",
  "description": "AI 및 머신러닝 프로젝트 담당",
  "hiringOrganization": {
    "@type": "Organization",
    "name": "기술 회사명"
  },
  "jobLocation": {
    "@type": "Place",
    "address": {
      "@type": "PostalAddress",
      "addressRegion": "서울",
      "addressCountry": "KR"
    }
  },
  "baseSalary": {
    "@type": "PriceSpecification",
    "currency": "KRW",
    "salary": "60000000"
  },
  "employmentType": "FULL_TIME",
  "datePosted": "2024-11-15",
  "validThrough": "2025-01-15"
}
```

### 6. CommunitySpecialist (커뮤니티/커뮤니케이션)
**필수 필드:**
- name: 커뮤니티명
- url: 웹사이트
- description: 설명

**권장 필드:**
- image: 로고/이미지
- about: 상세 정보
- aggregateRating: 평점
- potentialAction: 참여 방법

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "개발자 커뮤니티",
  "url": "https://dev-community.example.com",
  "description": "개발자들을 위한 정보 공유 플랫폼",
  "image": "https://dev-community.example.com/logo.jpg",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.4",
    "ratingCount": "3500"
  }
}
```

## 자주 함께 사용되는 스키마 조합

### 도서 + 저자 + 출판사
```json
{
  "@context": "https://schema.org",
  "@type": "Book",
  "name": "책제목",
  "url": "https://bookstore.example.com/book",
  "author": {
    "@type": "Person",
    "name": "저자명"
  },
  "publisher": {
    "@type": "Organization",
    "name": "출판사명"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.6",
    "ratingCount": "2000"
  }
}
```

### 부동산 매물 + 중개인 정보
```json
{
  "@context": "https://schema.org",
  "@type": "Residence",
  "name": "매물명",
  "url": "https://realestate.example.com/property",
  "address": {
    "@type": "PostalAddress",
    "addressRegion": "서울",
    "addressCountry": "KR"
  },
  "agent": {
    "@type": "RealEstateAgent",
    "name": "중개인명",
    "telephone": "02-1234-5678"
  }
}
```

### 채용공고 + 회사 정보
```json
{
  "@context": "https://schema.org",
  "@type": "JobPosting",
  "title": "직무명",
  "url": "https://careers.example.com/job",
  "hiringOrganization": {
    "@type": "Organization",
    "name": "회사명",
    "url": "https://company.example.com"
  },
  "jobLocation": {
    "@type": "Place",
    "address": {
      "@type": "PostalAddress",
      "addressCountry": "KR"
    }
  }
}
```

## 정보 산업 관련 중요 필드

| 필드 | 설명 | 예시 |
|------|------|------|
| isbn | 도서 식별 번호 | 978-1234567890 |
| numberOfPages | 책의 쪽수 | 320 |
| baseSalary | 급여 정보 | 60000000 KRW |
| validThrough | 마감일 | 2024-12-31 |
| floorSize | 면적 | 84 m² |
| price | 가격/매매가 | 600000000 KRW |

## 정보 콘텐츠 스키마 작성 팁
- 도서: 정확한 ISBN 및 출판 정보 포함
- 법률문서: 최신 버전 명시 및 업데이트 날짜 기재
- 부동산: 높은 품질의 사진 여러 장 포함
- 채용공고: 명확한 자격조건 및 근무 조건 기재
- 커뮤니티: 활성도 및 평점 정보 포함