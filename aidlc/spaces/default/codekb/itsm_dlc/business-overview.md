# ITSM Assistant 비즈니스 개요

## 비즈니스 도메인과 목적

이 저장소는 사내 IT 서비스 관리 시스템을 사용하는 직원을 위한 대화형 Assistant다. 자체 ITSM 업무 데이터를 소유하지 않고 기존 ITSM API에 HTTP로 연결하는 별도 FastAPI 서비스이며, 사용자가 선택한 계정의 서버 측 세션과 사용자 위임 토큰으로 권한·가시성을 유지한다.

현재 제품은 사용자 전환, 위임 토큰 발급·갱신, Agent 채팅, 대화 이력, 단일 페이지 웹 화면을 제공한다. Agent에는 아직 function tool이 없어서 티켓 업무 데이터는 조회하거나 변경하지 못한다.

## 주요 사용자와 가치

- 일반 사내 사용자: 테스트 계정을 선택하고 대화형 Assistant를 사용한다.
- 서비스 데스크 및 운영 역할: 같은 화면과 Agent를 사용하되 ITSM이 역할별 권한과 행 단위 가시성을 판정한다.
- 개발·운영 담당자: `.env.local` 설정, FastAPI 실행, DB 초기화와 pytest 테스트로 서비스를 운영·검증한다.

핵심 가치는 기존 ITSM 내부 구현과 결합하지 않으면서 현재 사용자 권한으로 안전한 대화 경험을 제공하는 것이다.

## 현재 제공 기능

| 기능 | 현재 동작 | 소유 구성요소 |
|---|---|---|
| 사용자 디렉터리 조회 | 서비스 토큰으로 활성 사용자 목록·상세 조회 | `ItsmAuthClient`, 세션 API |
| 사용자 전환 | 위임 토큰 발급, `/me` 검증, 새 서버 세션·대화 생성 | 세션·위임 토큰 관리 |
| 세션과 대화 이력 | HttpOnly 쿠키에는 세션 ID만, 사용자·토큰은 SQLite, 대화는 SDK SQLiteSession | SQLite 저장소, Agent 실행 서비스 |
| Agent 채팅 | 고정 모델·reasoning으로 Runner 실행, SDK 트레이싱 비활성 | Agent 정의, Agent 실행 서비스 |
| 웹 화면 | 사용자 전환, 채팅, 이력 초기화, 오류 표시 | 정적 웹 클라이언트 |
| 상태 확인 | ITSM 연결과 Agent 설정 상태 반환 | FastAPI 애플리케이션 팩토리 |

## ITSM 티켓 기능의 현재 공백

ITSM 계약에는 API v2 티켓 목록·상세·등록·수정이 있으나 애플리케이션에는 다음이 없다.

- Agent에 노출된 function tool
- 위임 토큰으로 티켓 업무 API를 호출하는 클라이언트 메서드
- 도구가 갱신 가능한 위임 인증을 얻는 서버 전용 capability
- 등록 멱등성과 수정 낙관적 잠금의 대화·저장 수명주기
- ITSM 원본 오류·비밀값을 모델과 사용자로부터 차단하는 티켓용 오류 DTO
- Fake ITSM 티켓 엔드포인트와 Agent tool-call 자동화 테스트

## 핵심 비즈니스 규칙

- 현재 사용자는 서버 세션으로만 결정하며 사용자 메시지나 모델 출력이 신원·역할을 바꾸지 못한다.
- 티켓 권한과 가시성은 사용자 위임 토큰을 받은 ITSM API가 최종 판정한다.
- 서비스 토큰은 디렉터리·카탈로그 용도이며 티켓 조회·변경에는 쓰지 않는다.
- 볼 수 없는 티켓은 실제 부재와 같은 404이므로 존재 여부를 추론하지 않는다.
- 등록은 위임 사용자와 멱등키에 결합되며 같은 키·같은 본문은 기존 결과를 재사용한다.
- 수정은 현재 version의 `If-Match`가 필요하고 충돌 시 자동 덮어쓰지 않는다.
- 고정 모델·reasoning, 사용자 전환, 세션, 대화 이력과 기존 API/UI 계약은 보존 대상이다.

## 시스템 경계

저장소가 소유하는 것은 Assistant 애플리케이션, 서버 세션 DB, Agent 대화 이력, 정적 화면과 테스트 대역이다. ITSM 티켓·카탈로그·디렉터리·권한 정책은 외부 ITSM 시스템이 소유하며 계약 기준은 `docs/itsm/integration-guide.md`와 `docs/itsm/openapi.json`이다. OpenAI 모델 호출은 Agents SDK가 담당한다.

## 주요 근거

- 애플리케이션 개요와 실행 계약: `README.md`
- 서버 세션과 위임: `app/session.py`, `app/db.py`
- 현재 Agent 경계: `app/agent/assistant.py`, `app/agent/context.py`, `app/agent/service.py`
- ITSM 계약: `docs/itsm/integration-guide.md`, `docs/itsm/openapi.json`
- 네트워크 없는 자동화 기반: `tests/conftest.py`, `tests/test_agent.py`, `tests/test_session.py`
