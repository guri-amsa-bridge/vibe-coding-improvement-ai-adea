# Impact Map

**바이브 코딩 환경을 위한 변경 영향도 자동 분석 프레임워크**

---

## 문제 정의

LLM 기반 바이브 코딩 환경에서는 코드 작성과 수정 속도가 비약적으로 증가하지만, 그에 비례해 **변경 코드의 영향 범위를 정확히 인지하지 못한 채 배포되는 문제**가 빈번하게 발생합니다.

개발자는 자연어 지시를 통해 다수의 파일과 로직을 동시에 수정하며, 이 과정에서 함수 호출 관계, 데이터 흐름, 설정 의존성, 외부 인터페이스 변화에 대한 인지 없이 코드가 생성됩니다. 변경 사항이 실제로 **어떤 API, 어떤 서비스, 어떤 데이터에 영향을 미치는지**를 개인의 경험이나 PR 리뷰에만 의존하게 되며, 이는 대규모 시스템일수록 위험도를 급격히 증가시킵니다.

> 바이브 코딩은 **속도를 얻는 대신, 시스템 전체에 대한 통제력을 잃는 구조적 문제**를 내포하고 있습니다.

### 원인 분석

| 원인 | 설명 |
|------|------|
| 변경 중심 개발의 한계 | 변경 단위가 커지고 빈도가 높아져, 인간이 영향도를 직관적으로 판단하기 어려운 규모가 됨 |
| 아키텍처 정보의 비가시화 | 코드·DB·설정·외부 API 간의 관계가 기계 해석 가능한 형태로 정리되어 있지 않음 |
| 영향 분석의 비정형성 | 체크리스트, 경험, 리뷰 코멘트 등 비정형적·주관적 방식에 의존하고 있음 |

---

## 해결 방식

Impact Map은 **정적 분석 기반 변경 영향도 맵 프레임워크**로 이 문제를 해결합니다.

> **변경된 코드(diff)** 를 입력으로 받아, **해당 변경이 시스템 전반에 미칠 수 있는 영향 범위**를 호출 관계·데이터 흐름·설정 의존성 관점에서 **자동 산출·가시화**합니다.

### 2-Agent 구조

```
┌──────────────────────┐    architecture_map.json    ┌──────────────────────┐
│  Architecture Mapper  │ ─────────────────────────▶ │  Impact Analyzer      │
│  (Sub Agent)          │                             │  (Main Agent)         │
│                       │    git diff (patch)         │                       │
│  • 소스 파일 스캔       │ ◀───────────────────────── │  • diff 파싱           │
│  • import/require 분석 │                             │  • 그래프 BFS 탐색      │
│  • 의존성 그래프 출력    │                             │  • 위험도 동적 판단      │
│    (인접 리스트 JSON)   │                             │  • Impact Report 생성  │
└──────────────────────┘                             └──────────────────────┘
```

- **Architecture Mapper**: Python `ast` + JS 정규식으로 파일 간 import 관계를 추출하여 의존성 그래프를 생성
- **Impact Analyzer**: diff에서 변경 파일을 추출하고, 의존성 그래프를 BFS 탐색하여 영향 전파 경로와 위험도를 자동 산출

---

## 구현된 기능

### 1) 아키텍처 의존성 자동 스캔

프로젝트 소스 코드를 스캔하여 파일 간 **의존성 참조 그래프를 자동 구축**합니다.

```bash
python3 agents/architecture_mapper.py --scan-all --root <프로젝트경로>
python3 agents/architecture_mapper.py --target src/auth.py --root <프로젝트경로>
```

### 2) 변경 영향도 자동 분석

diff를 입력받아 아키텍처 맵과 대조하여 **영향 범위를 자동 산출**합니다. 위험도는 영향 노드 수와 핵심 모듈 포함 여부에 따라 동적으로 결정됩니다.

```bash
python3 agents/impact_analyzer.py --diff changes.patch --map architecture_map.json
```

리포트에는 다음이 포함됩니다:
- 전체 위험도 등급 (🔴 High / 🟡 Medium / 🟢 Low)
- 확정된 영향 범위: API·서비스·인프라·프론트엔드 계층별 분류
- 영향 전파 경로 (어떤 파일이 어떤 경로로 영향받는지)
- 에이전트 조치 권고: DB 마이그레이션, Fallback 코드, 리뷰어 승인 등

### 3) 영향도 시각화 (Web Viewer)

의존성 그래프를 **인터랙티브 웹 UI**로 시각화합니다. 변경 시뮬레이션 시 Blast Radius가 실시간으로 표시됩니다.

```bash
python3 -m http.server 8000
# 브라우저에서 http://localhost:8000/ui/ 접속
```

### 4) Zero-Prompt 자동화 (자동 방어 체계)

개발자가 별도 분석 명령을 내리지 않아도 **배포 전 자동 안전장치**가 작동합니다.

- **Claude Code Hook**: AI 에이전트가 커밋 시도 시 시스템이 자동 인터셉트, 고위험 감지 시 차단
- **Git Pre-commit**: IDE나 터미널에서 직접 커밋 시에도 자동 영향도 스캔 수행

### 5) CI/CD 파이프라인 자동 연동

PR 생성 시 GitHub Actions가 자동으로 아키텍처 맵 생성 → 영향도 분석 → 리포트를 PR 코멘트로 등록합니다.

### 6) Cross-Agent 지원 (Tool-Agnostic)

특정 AI 도구에 종속되지 않는 **범용 워크플로우 체계**를 제공합니다. Cursor(`.cursorrules`), Claude Code(Skills/Hooks), Antigravity 등 주요 AI 에디터에서 동일한 3-Phase 프로세스가 적용됩니다.

---

## 다층 방어 체계

단일 검증 지점이 아닌 **4단계 다층 방어 구조**로, 어느 단계에서 누락되더라도 다음 단계에서 잡아냅니다.

| 층 | 방어 지점 | 메커니즘 | 동작 방식 |
|----|----------|----------|----------|
| 1층 | AI 에디터 내부 | Skills/Rules 기반 사전 인지 | AI가 코드 수정 전 의존성 자동 스캔 |
| 2층 | 커밋 시점 | Claude Hook / Git Pre-commit | 고위험 변경 커밋 자동 차단 |
| 3층 | PR 시점 | GitHub Actions CI/CD | PR에 Impact Report 자동 코멘트 |
| 4층 | 리뷰 시점 | 시각화 UI + 리포트 | 리뷰어가 Blast Radius를 시각적 확인 |

---

## 데모 실행

```bash
bash examples/run_demo.sh
```

예시 프로젝트(Python+JS 웹앱)를 대상으로 4가지 시나리오의 영향도 분석을 수행합니다.

| 시나리오 | 변경 대상 | 영향 범위 | 위험도 |
|----------|----------|----------|--------|
| UI 텍스트 수정 | `renderer.js` | 직접 1개 | 🟢 Low |
| 서비스 로직 변경 | `item_service.py` | 직접 1개 (API 계층) | 🟡 Medium |
| DB 엔진 교체 | `database.py` | 직접 3개 + 간접 1개 | 🔴 High |
| 인증 알고리즘 변경 | `auth.py` | 직접 2개 (API + 서비스) | 🔴 High |

---

## 기대 효과

- **장애 예방**: 배포 전 영향 범위 사전 인지로 장애 발생률 감소
- **리뷰 효율 향상**: 리뷰어가 "어디를 봐야 하는지" 명확히 인지
- **운영 안정성 강화**: 설정·권한·외부 인터페이스 변경 리스크 조기 발견
- **바이브 코딩 신뢰성 확보**: 속도는 유지하면서 안전성 보완
- **에이전트 간 상호 검증**: 코드 생성 AI와 검증 AI의 분리를 통한 구조적 안전성

---

## 프로젝트 구조

```
├── agents/                         # 핵심 에이전트
│   ├── architecture_mapper.py      # (Sub) 의존성 그래프 생성
│   └── impact_analyzer.py          # (Main) 변경 영향도 분석
├── examples/                       # 데모용 예시 프로젝트
│   ├── sample_project/             # Python+JS 웹앱 예시 소스
│   ├── diffs/                      # Low/Medium/High 시나리오 diff
│   └── run_demo.sh                 # 원클릭 데모 실행
├── ui/                             # 영향도 시각화 Web UI
├── .claude/                        # Claude Code 통합 (Skills, Hooks)
├── .githooks/                      # Git pre-commit 자동 검사
├── .github/workflows/              # GitHub Actions CI/CD
├── .cursorrules                    # Cursor AI 에이전트 규칙
└── docs/                           # 상세 문서
```

## 문서

| 문서 | 내용 |
|------|------|
| [시작 가이드](docs/getting-started.md) | 설치, CLI 옵션, Hook 활성화 방법 |
| [아키텍처 설계](docs/architecture.md) | 2-Agent 구조, 위험도 판단 기준, 데이터 흐름 |
| [CI/CD 연동](docs/ci-cd.md) | GitHub Actions 파이프라인 설정 |
| [Cross-Agent 지원](docs/cross-agent.md) | Cursor, Claude Code, Antigravity 통합 방식 |
| [Hook 자동 방어](docs/hooks.md) | PreToolUse Hook, Git pre-commit 설정 |
| [AI 워크플로우](docs/AI_WORKFLOW.md) | AI 어시스턴트 공통 3-Phase 워크플로우 |
| [Claude Code 예시](docs/claude_code_example.md) | Claude Code CLI 사용 시나리오 |

## 기술 스택

| 영역 | 기술 |
|------|------|
| 의존성 분석 | Python `ast`, 정규식 (표준 라이브러리만 사용) |
| 그래프 탐색 | BFS (`collections.deque`) |
| 시각화 | vis-network, Tailwind CSS |
| CI/CD | GitHub Actions |
| 자동화 | Bash Shell Script (Hook) |

## 한계 및 확장 가능성

### 현재 한계

- 정적 분석 기반으로, 동적 로딩·런타임 분기·Feature Flag 기반 로직은 분석에 한계 존재
- 외부 SaaS의 실제 동작이나 실시간 상태는 완전한 추론 불가
- 현재 Python과 JS/TS만 지원

### 확장 가능성

- **Tree-sitter 기반 다중 언어 지원**: Java, Go, Rust 등 추가 언어 확장
- **LLM 기반 의미 분석**: 변경 코드의 맥락적 영향 추론
- **런타임 트레이싱 결합**: 정적 + 동적 분석 하이브리드
- **보안 영향 분석**: 권한 상승, 데이터 노출 가능성 자동 감지
- **변경 이력 기반 사고 예측**: 고위험 패턴 사전 감지 모델
