# AlgoAgent

> **LangChain Tool-Calling Agent** 기반의 알고리즘 학습 튜터
> 백준 아이디와 학습 목표를 입력하면, AI가 실력을 분석하고 맞춤 문제 로드맵을 자동으로 생성합니다.

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| **실력 분석** | 백준 아이디로 알고리즘 태그별 레이팅 조회 (solved.ac API) |
| **목표별 가이드** | 취업 / 취미 / 대회 목표에 맞는 핵심 알고리즘 제시 |
| **문제 추천** | 난이도·태그 기반으로 solved.ac에서 문제 자동 검색 |
| **로드맵 저장** | 추천 문제를 MongoDB에 저장해 학습 로드맵으로 관리 |
| **세션 관리** | 채팅 세션별 독립적인 대화 이력 및 로드맵 유지 |

---

## 아키텍처

```
사용자 메시지
     │
     ▼
FastAPI (POST /sendmessage)
     │
     ▼
LangChain AgentExecutor
  ├─ [Tool] fetch_beakjoon           → solved.ac 태그별 레이팅 조회
  ├─ [Tool] get_goal_requirements    → 목표(취업/취미/대회) 가이드 반환
  ├─ [Tool] search_problem_from_solvedac → 난이도·태그로 문제 검색
  └─ [Tool] recommand_question       → 문제 메타데이터 조회 후 MongoDB 저장
     │
     ▼
GPT 최종 응답 생성
     │
     ├─→ PostgreSQL  (메시지·세션 저장)
     └─→ MongoDB     (학습 로드맵 저장)
```

### Agent Tool 상세

| Tool | 입력 | 역할 |
|------|------|------|
| `fetch_beakjoon` | 백준 아이디 | solved.ac `/user/tag_ratings` 호출 → 태그별 레이팅 반환 |
| `get_goal_requirements` | `취업` / `취미` / `대회` | 목표별 핵심 태그·목표 티어·우선순위 반환 |
| `search_problem_from_solvedac` | tag, tier 범위 | solved.ac `/search/problem` 호출 → 문제 번호·제목 반환 |
| `recommand_question` | 문제 번호 | 문제 메타데이터 조회 후 세션 로드맵에 `$push` |

### 기술적 구현 포인트

- **ContextVar로 세션 ID 전달**: `AgentExecutor`가 `RunnableConfig`를 Tool에 전달하지 않는 LangChain 한계를, Python `contextvars.ContextVar`로 해결
- **완전 비동기 파이프라인**: `ainvoke()` + `httpx.AsyncClient` + `Motor` (MongoDB 비동기 드라이버)
- **멀티 DB 전략**: 트랜잭션이 필요한 유저·세션 데이터는 PostgreSQL, 유동적인 문제 배열은 MongoDB
- **자동 세션 제목 생성**: 첫 메시지를 별도 LLM chain으로 요약해 제목 설정

---

## 기술 스택

**Backend**
- Python 3.11
- FastAPI + Uvicorn
- LangChain (`create_tool_calling_agent` + `AgentExecutor`)
- OpenAI GPT (gpt-4.5-nano)

**Database**
- PostgreSQL + SQLAlchemy (유저, 채팅 세션, 메시지)
- MongoDB + Motor (학습 로드맵)

**External API**
- [solved.ac API v3](https://solvedac.github.io/unofficial-documentation/)

**Frontend**
- React (Vite, 포트 5173)

---

## API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/login` | 닉네임 기반 로그인 / 회원가입 |
| `POST` | `/sendmessage` | 메시지 전송 및 AI Agent 응답 |
| `GET` | `/getsessions?user_id=` | 사용자의 채팅 세션 목록 조회 |
| `GET` | `/getMessages?session_id=` | 세션의 메시지 이력 조회 |
| `GET` | `/getLoadmap?session_id=` | 세션의 학습 로드맵 조회 |

---

## 시작하기

### 1. 환경 변수 설정

`.env` 파일을 프로젝트 루트에 생성합니다.

```env
OPENAI_API_KEY=sk-proj-...
DB_ACCESS_URL=postgresql://user:password@host:5432/dbname
MONGODB_ACCESS_URL=mongodb+srv://user:password@cluster/dbname
```

### 2. 백엔드 실행

```bash
# 가상환경 생성 및 진입
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows
source .venv/bin/activate       # macOS / Linux

# 의존성 설치
pip install -r requirements.txt

# 서버 시작 (포트 8000)
uvicorn main:app --reload
```

### 3. 프론트엔드 실행

```bash
npm install
npm run dev   # 포트 5173
```

---

## 프로젝트 구조

```
algoAgent/
├── main.py           # FastAPI 앱, API 엔드포인트, Agent 설정
├── tools.py          # LangChain Tool 4종 정의
├── agent_context.py  # ContextVar (Tool에 session_id 전달)
├── models.py         # SQLAlchemy ORM 모델 (User, ChatSession, Message)
├── schemas.py        # Pydantic 스키마, MongoDB StudySession 문서 구조
├── database.py       # PostgreSQL 세션 설정
├── mongodb.py        # MongoDB 연결 및 컬렉션 접근
├── hook.py           # LangChain callback hook
└── requirements.txt
```
