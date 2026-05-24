# UX Simulation Server

AI 기반 UX 리서치 시뮬레이션 서버입니다. 페르소나 생성, Individual 인터뷰, FGI (Focus Group Interview), 저니맵 생성 기능을 제공합니다.

## 기능

### 1. 페르소나 관리 (Persona)
- 페르소나 유효성 검증
- AI 기반 페르소나 자동 생성

### 2. Individual 인터뷰 시뮬레이션
- 1:1 인터뷰 시뮬레이션
- 스트리밍 응답 지원

### 3. FGI (Focus Group Interview)
- 다중 페르소나 그룹 인터뷰
- 모더레이터 포함
- 참가자 간 상호작용
- 스트리밍 응답 지원

### 4. 저니맵 생성 (Journey Map)
- 목표 기반 사용자 여정 시뮬레이션
- 이전 인터뷰 결과 컨텍스트 활용
- CSV 포맷 변환

## 기술 스택

- **Backend**: Django + Django REST Framework
- **Database**: Supabase (PostgreSQL)
- **Auth**: Supabase Authentication (Google, Email)
- **AI**: Google Gemini API

## 설치

### 1. 가상환경 생성 및 활성화

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or
.\venv\Scripts\activate  # Windows
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정

```bash
cp .env.example .env
# .env 파일을 편집하여 실제 값 입력
```

### 4. 마이그레이션

```bash
python manage.py migrate
```

### 5. 서버 실행

```bash
python manage.py runserver
```

## API 엔드포인트

### Health Check
```
GET /api/health/
```

### 사용자
```
GET /api/users/profile/        # 프로필 조회 (인증 필요)
POST /api/users/verify/        # 토큰 검증
```

### 페르소나
```
POST /api/simulation/persona/validate/    # 페르소나 유효성 검증
POST /api/simulation/persona/generate/    # AI 페르소나 생성
```

### Individual 인터뷰
```
POST /api/simulation/individual/run/      # 인터뷰 실행
POST /api/simulation/individual/stream/   # 인터뷰 실행 (스트리밍)
```

### FGI
```
POST /api/simulation/fgi/run/             # FGI 실행
POST /api/simulation/fgi/stream/          # FGI 실행 (스트리밍)
```

### 저니맵
```
POST /api/simulation/journey/generate/    # 저니맵 생성
POST /api/simulation/journey/stream/      # 저니맵 생성 (스트리밍)
POST /api/simulation/journey/csv/         # 저니맵 → CSV 변환
```

## 요청 예시

### 페르소나 생성
```json
POST /api/simulation/persona/generate/
{
  "context": "20-30대 직장인 대상 이커머스 앱 사용자",
  "count": 3
}
```

### Individual 인터뷰
```json
POST /api/simulation/individual/run/
{
  "persona": {
    "id": "p_01",
    "name": "김영희",
    "age": 28,
    "gender": "female",
    "segment": "early",
    "background": "IT 회사 마케터",
    "occupation": "Marketer",
    "goals": ["효율적인 쇼핑", "좋은 거래 찾기"],
    "pains": ["복잡한 검색", "신뢰할 수 없는 리뷰"]
  },
  "questionnaire": {
    "id": "q_01",
    "title": "쇼핑 경험 인터뷰",
    "instructions": "자세한 답변 부탁드립니다",
    "questions": [
      {"id": "q1", "text": "최근 온라인 쇼핑 경험을 말씀해주세요", "kind": "open"},
      {"id": "q2", "text": "장바구니 기능의 만족도는?", "kind": "scale", "scale_min": 1, "scale_max": 7}
    ]
  },
  "max_questions": 2
}
```

### FGI 실행
```json
POST /api/simulation/fgi/run/
{
  "personas": [
    {"id": "p_01", "name": "김영희", "age": 28, ...},
    {"id": "p_02", "name": "이철수", "age": 35, ...}
  ],
  "questionnaire": {...},
  "scenario": {
    "id": "s_01",
    "title": "이커머스 장바구니 사용",
    "description": "온라인 쇼핑몰 장바구니 기능에 대한 토론"
  },
  "max_rounds": 3
}
```

### 저니맵 생성
```json
POST /api/simulation/journey/generate/
{
  "goal": "여름 이불 최저가로 구매하기",
  "persona": {...},
  "fgi_transcript": {...},
  "individual_transcript": {...}
}
```

## 인증

모든 시뮬레이션 API는 Supabase JWT 토큰 인증이 필요합니다.

```
Authorization: Bearer <supabase_access_token>
```

## 프로젝트 구조

```
Server/
├── config/              # Django 설정
│   ├── settings.py
│   ├── urls.py
│   └── exceptions.py
├── users/               # 사용자 인증 앱
│   ├── authentication.py   # Supabase JWT 인증
│   ├── supabase_client.py
│   ├── views.py
│   └── urls.py
├── simulation/          # 시뮬레이션 앱
│   ├── services/           # 비즈니스 로직
│   │   ├── gemini_client.py
│   │   ├── persona_service.py
│   │   ├── individual_service.py
│   │   ├── fgi_service.py
│   │   └── journey_service.py
│   ├── types/              # Pydantic 모델
│   │   └── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── .env.example
├── requirements.txt
└── manage.py
```

## 라이선스

MIT
