---
name: "산업군: 교육"
description: "교육 부문(유아, 육아, 전문, 학교)의 JSON-LD 스키마 작성 가이드"
---

# 교육 (Education) - JSON-LD 스키마 작성 가이드

## 기본 스키마 타입

### 1. EducationalOrganization (교육 기관)
**필수 필드:**
- name: 기관명
- url: 웹사이트
- address: 주소

**권장 필드:**
- image: 로고/대표 이미지
- telephone: 전화번호
- description: 기관 설명
- foundingDate: 설립일
- alumniOf: 동문

### 2. Course (강좌/교과)
**필수 필드:**
- name: 강좌명
- url: 강좌 페이지
- provider: 제공 기관

**권장 필드:**
- description: 강좌 설명
- educationLevel: 교육 수준
- numberOfCredits: 학점
- coursePrerequisites: 선수과목
- instructor: 강사 정보

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Course",
  "name": "기초 수학",
  "url": "https://example.edu/course/math-101",
  "description": "고등학교 1학년 수학",
  "educationLevel": "High School",
  "provider": {
    "@type": "EducationalOrganization",
    "name": "예시 고등학교"
  },
  "instructor": {
    "@type": "Person",
    "name": "김교사"
  }
}
```

### 3. OnlineCourse (온라인 강좌)
**필수 필드:**
- name: 강좌명
- url: 강좌 페이지
- provider: 제공 기관

**권장 필드:**
- description: 강좌 설명
- courseCode: 강좌 코드
- learningResourceType: 학습 자료 유형
- duration: 코스 기간

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "OnlineCourse",
  "name": "Python 프로그래밍",
  "url": "https://example.edu/courses/python",
  "description": "초급 파이썬 강좌",
  "provider": {
    "@type": "Organization",
    "name": "온라인 학습 플랫폼"
  },
  "instructor": {
    "@type": "Person",
    "name": "이교사"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "ratingCount": "1250"
  }
}
```

### 4. SchoolEvent (학교 행사)
**필수 필드:**
- name: 행사명
- startDate: 시작일
- location: 장소

**권장 필드:**
- description: 행사 설명
- endDate: 종료일
- image: 행사 이미지
- organizer: 주최 기관
- eventSchedule: 세부 일정

### 5. Course (유아/육아 교육)
**필수 필드:**
- name: 프로그램명
- url: 페이지
- ageRange: 대상 연령

**권장 필드:**
- numberOfCredits: 주차/회차
- coursePrerequisites: 선행 요구사항
- learningResourceType: 학습 자료 유형

**예제:**
```json
{
  "@context": "https://schema.org",
  "@type": "Course",
  "name": "영유아 영어 놀이 수업",
  "url": "https://example.edu/preschool/english",
  "ageRange": "2-5",
  "description": "노래와 게임으로 배우는 영어",
  "provider": {
    "@type": "EducationalOrganization",
    "name": "예시 유치원"
  }
}
```

## 자주 함께 사용되는 스키마 조합

### 기관 + 여러 강좌
```json
[
  {
    "@type": "EducationalOrganization",
    "name": "대학교명",
    "url": "https://example.edu"
  },
  {
    "@type": "Course",
    "name": "강좌명",
    "provider": { "@type": "EducationalOrganization", "name": "대학교명" }
  },
  {
    "@type": "Course",
    "name": "다른 강좌명",
    "provider": { "@type": "EducationalOrganization", "name": "대학교명" }
  }
]
```

### 온라인 강좌 + 평점
```json
{
  "@context": "https://schema.org",
  "@type": "OnlineCourse",
  "name": "강좌명",
  "url": "https://example.edu/course",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.5",
    "ratingCount": "500",
    "bestRating": "5",
    "worstRating": "1"
  }
}
```

## 교육 수준 (educationLevel) 표준 값
- "Preschool"
- "Elementary School"
- "Middle School"
- "High School"
- "Vocational"
- "Associate's degree"
- "Bachelor's degree"
- "Master's degree"
- "Doctoral degree"