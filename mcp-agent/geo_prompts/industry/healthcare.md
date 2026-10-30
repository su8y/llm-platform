---
name: "산업군: 의료"
description: "의료 부문(의료 서비스, 전문 의료, 제약, 종합 의료)의 JSON-LD 스키마 작성 가이드"
---

# 의료 (Healthcare) - JSON-LD 스키마 작성 가이드

## 기본 스키마 타입

### 1. MedicalBusiness (의료기관)
**필수 필드:**
- name: 기관명
- url: 웹사이트
- address: 주소
- telephone: 전화번호

**권장 필드:**
- image: 로고/사진
- description: 기관 설명
- aggregateRating: 평점
- medicalSpecialty: 전문분야
- openingHoursSpecification: 운영 시간
- email: 이메일

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "MedicalBusiness",
  "name": "의료센터",
  "url": "https://medical.example.com",
  "image": "https://medical.example.com/logo.jpg",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "의료로 123",
    "addressRegion": "서울",
    "addressCountry": "KR"
  },
  "telephone": "02-1234-5678",
  "medicalSpecialty": ["Cardiology", "Orthopedics"],
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.5",
    "ratingCount": "850"
  }
}
```

### 2. Doctor (의사)
**필수 필드:**
- name: 의사명
- url: 프로필 페이지
- affiliation: 소속 의료기관

**권장 필드:**
- image: 사진
- description: 경력/소개
- medicalSpecialty: 전문분야
- credential: 자격증
- telephone: 진료 연락처
- award: 수상 경력

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Doctor",
  "name": "김의사",
  "url": "https://medical.example.com/doctor-kim",
  "image": "https://medical.example.com/dr-kim.jpg",
  "medicalSpecialty": "Cardiology",
  "affiliation": {
    "@type": "MedicalBusiness",
    "name": "의료센터"
  },
  "credential": "M.D. from Seoul National University"
}
```

### 3. MedicalCondition (질환 정보)
**필수 필드:**
- name: 질환명
- url: 정보 페이지
- description: 설명

**권장 필드:**
- symptom: 증상
- possibleTreatment: 치료법
- riskFactor: 위험 요소
- stageSuffix: 단계

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "MedicalCondition",
  "name": "고혈압",
  "url": "https://medical.example.com/hypertension",
  "description": "혈압이 정상 수치보다 높은 상태",
  "symptom": [
    "두통",
    "피로감",
    "호흡곤란"
  ],
  "possibleTreatment": [
    { "@type": "MedicalTherapy", "name": "약물 치료" },
    { "@type": "MedicalTherapy", "name": "생활 습관 개선" }
  ]
}
```

### 4. MedicalProcedure (의료 시술)
**필수 필드:**
- name: 시술명
- url: 정보 페이지
- description: 설명

**권장 필드:**
- image: 이미지
- expectedOutcome: 예상 결과
- preparation: 준비 사항
- recovery: 회복 정보
- procedureType: 시술 유형
- followUp: 사후 관리

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "MedicalProcedure",
  "name": "백내장 수술",
  "url": "https://medical.example.com/cataract-surgery",
  "description": "렌즈를 인공 렌즈로 교체하는 시술",
  "procedureType": "Surgical",
  "preparation": "수술 전 안약 처방",
  "recovery": "1-2주 회복 기간"
}
```

### 5. MedicalTherapy (치료법)
**필수 필드:**
- name: 치료명
- description: 설명

**권장 필드:**
- url: 상세 페이지
- image: 이미지
- applicableFor: 대상 질환
- adverseOutcome: 부작용

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "MedicalTherapy",
  "name": "물리치료",
  "description": "신체 재활을 돕는 치료",
  "applicableFor": {
    "@type": "MedicalCondition",
    "name": "근육 손상"
  }
}
```

### 6. Medicine (약물/처방약)
**필수 필드:**
- name: 약명
- url: 약물 정보 페이지

**권장 필드:**
- description: 설명
- drugClass: 약물 분류
- activeIngredient: 유효성분
- adverseOutcome: 부작용
- dosageForm: 제형 (정제, 캡슐 등)

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Medicine",
  "name": "감기약",
  "url": "https://medical.example.com/medicine-abc",
  "drugClass": "Cold Medicine",
  "activeIngredient": "Acetaminophen",
  "dosageForm": "Tablet"
}
```

## 자주 함께 사용되는 스키마 조합

### 의료기관 + 의사 + 전문분야
```json
[
  {
    "@type": "MedicalBusiness",
    "name": "병원명",
    "url": "https://hospital.example.com",
    "medicalSpecialty": ["Cardiology"]
  },
  {
    "@type": "Doctor",
    "name": "의사명",
    "medicalSpecialty": "Cardiology",
    "affiliation": { "@type": "MedicalBusiness", "name": "병원명" }
  }
]
```

### 질환 + 증상 + 치료법
```json
{
  "@context": "https://schema.org",
  "@type": "MedicalCondition",
  "name": "당뇨병",
  "url": "https://medical.example.com/diabetes",
  "symptom": ["과음수", "피로", "체중감소"],
  "possibleTreatment": [
    { "@type": "MedicalTherapy", "name": "인슐린 치료" },
    { "@type": "MedicalTherapy", "name": "운동 및 식이요법" }
  ]
}
```

### 진료 예약 정보
```json
{
  "@context": "https://schema.org",
  "@type": "MedicalBusiness",
  "name": "의료기관",
  "url": "https://medical.example.com",
  "openingHoursSpecification": {
    "@type": "OpeningHoursSpecification",
    "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "opens": "09:00",
    "closes": "18:00"
  }
}
```

## 의료 관련 주요 필드

| 필드 | 설명 | 예시 |
|------|------|------|
| medicalSpecialty | 진료 전문분야 | Cardiology, Orthopedics |
| aggregateRating | 환자 평점 | 4.7/5.0 |
| symptom | 증상 | 두통, 피로 |
| credential | 의료자격 | M.D., Ph.D. |
| dosageForm | 약의 제형 | Tablet, Capsule |
| preparation | 사전 준비 | 금식 필요 |

## 의료 데이터 신뢰성 주의사항
- 정확한 의료 정보 기반 작성 필수
- 전문 용어는 표준 의료 용어 사용
- 한국 의료 환경에 맞게 조정 (병원, 의원, 한의원 등)
- 법적 책임 고려 필요