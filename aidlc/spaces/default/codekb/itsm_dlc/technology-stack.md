# ITSM Assistant 기술 스택

## Runtime

| 기술 | 버전 | 용도 | 근거 |
|---|---:|---|---|
| Python | 3.13 | 서버, scripts, tests | `.python-version` |
| 브라우저 JavaScript | 빌드 없음 | 사용자 전환·채팅 UI | `static/app.js` |
| HTML/CSS | 표준 | 단일 페이지 화면 | `static/index.html`, `static/style.css` |
| SQLite | Python/SDK 포함 | 서버 세션과 Agent 대화 이력 | `app/db.py`, `AgentService._session()` |

## Application Frameworks

| 패키지 | 고정 버전 | 용도 |
|---|---:|---|
| FastAPI | 0.162.0 | ASGI HTTP API, dependency injection, response model |
| Uvicorn | 0.54.0 | ASGI 실행 서버 |
| Pydantic | 2.14.1 | API schema와 입력 검증 |
| Starlette | 1.10.0 | FastAPI 하위 HTTP/정적 파일/TestClient 기반 |

## AI and Integration

| 패키지 | 고정 버전 | 용도 |
|---|---:|---|
| openai-agents | 0.24.0 | `Agent`, `Runner`, `ModelSettings`, `SQLiteSession`, 향후 `function_tool` |
| openai | 3.37.0 | `AsyncOpenAI`, `OpenAIResponsesModel`, 오류 타입 |
| httpx | 0.28.1 | ITSM AsyncClient, scripts client, MockTransport 테스트 |
| python-dotenv | 1.2.4 | `.env.local` 설정 로드 |

Agent의 애플리케이션 설정은 모델 `gpt-6-luna`, reasoning effort `high`로 고정되어 있다. 이는 패키지 버전이 아니라 프로젝트 상수이며 자동 fallback이 없다.

## Testing and Quality

| 기술 | 버전/상태 | 용도 |
|---|---|---|
| pytest | 9.1.1 | 테스트 실행 |
| FastAPI TestClient | Starlette 포함 | 앱 HTTP 통합 테스트 |
| `httpx.MockTransport` | httpx 포함 | 외부 ITSM 네트워크 차단과 계약 대역 |
| FakeModel | 프로젝트 test double | 실제 OpenAI 없이 Agents SDK Runner 실행 |
| Coverage | 구성 없음 | 정량 line coverage는 현재 저장소에 기록되지 않음 |
| Linter/Formatter | 구성 없음 | 별도 Ruff/Black 설정 없음 |
| CI/CD | 구성 없음 | 프로젝트 소유 pipeline 파일 없음 |

## Package Management

- `requirements.in`에 직접 의존성을 정확한 버전으로 선언한다.
- `requirements.txt`는 Python 3.13 대상으로 uv compile한 transitive lock 목록이다.
- 권장 설치는 uv virtual environment와 `uv pip install`이다.
- `pyproject.toml`, package build metadata, JavaScript package manager는 없다.

## Configuration and Secrets

- `Settings`는 frozen dataclass이며 `.env.local`과 일부 환경 변수를 읽는다.
- OpenAI API key는 `.env.local`에서만 읽고 `os.environ`에 쓰지 않는다.
- ITSM URL/client credentials/timeout은 환경 변수 우선, `.env.local`, 개발 기본값 순서다.
- API key와 client secret field는 `repr=False`지만 이것만으로 로그·오류 누출을 막지는 못한다.
- `.env.local`과 runtime `data/`는 gitignore 대상이다.

## External Systems

| 시스템 | 계약 | 인증 | 역할 |
|---|---|---|---|
| ITSM API | OpenAPI 3.1, API version 2.4.0 | service 또는 user-delegation bearer | 디렉터리, 권한·가시성, 티켓 업무 원장 |
| OpenAI Responses API | OpenAI SDK/Agents SDK | OpenAI API key | Agent 모델 추론 |
| 브라우저 | same-origin HTTP | HttpOnly session cookie | 사용자 UI |

## 호환성·운영 특성

- 단일 프로세스 앱이지만 httpx AsyncClient와 SQLite connections를 요청·앱 수명주기에 맞게 사용한다.
- 정적 클라이언트는 bundler/transpiler 없이 최신 브라우저 표준을 사용한다.
- ITSM v1은 계약 문서에만 있고 앱 구현은 v2만 사용한다.
- 배포 manifest, container, cloud IaC는 없다.
