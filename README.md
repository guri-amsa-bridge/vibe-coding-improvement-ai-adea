# Impact Map

**바이브 코딩 환경을 위한 변경 영향도 자동 분석 프레임워크**

AI(LLM) 기반 바이브 코딩은 개발 속도를 비약적으로 높여주지만, 변경 코드의 영향 범위를 인지하지 못한 채 배포되는 문제를 야기합니다. Impact Map은 **코드 변경(diff)을 입력받아 시스템 전반의 영향 범위를 자동 산출**하는 프레임워크입니다.

---

## 핵심 기능

| 기능 | 설명 |
|------|------|
| **아키텍처 의존성 스캔** | Python AST + JS 정규식으로 파일 간 import 관계를 자동 분석 |
| **변경 영향도 분석** | diff 파싱 → 의존성 그래프 BFS 탐색 → 동적 위험도 판단 (Low/Medium/High) |
| **4층 다층 방어** | AI 에디터 → Git Hook → CI/CD → Web UI 시각화까지 단계별 자동 검증 |
| **Cross-Agent 지원** | Cursor, Claude Code, Antigravity 등 AI 도구에 종속되지 않는 공통 워크플로우 |

## 빠른 시작

```bash
# 데모 실행 (예시 프로젝트 + 4가지 시나리오)
bash examples/run_demo.sh
```

```bash
# 직접 사용
python3 agents/architecture_mapper.py --scan-all --root <프로젝트경로>
git diff > changes.patch
python3 agents/impact_analyzer.py --diff changes.patch
```

## 데모 결과 예시

```
📌 database.py 변경 시 (DB 엔진 교체)

  변경 파일: 1개 (src/database.py)
  영향 범위: 4개 (직접 3개 + 간접 1개)
  전체 위험도: 🔴 High

  영향 전파 경로:
    src/database.py → src/auth.py → api/routes.py
    src/database.py → src/item_service.py
    src/database.py → src/user_service.py
```

## 프로젝트 구조

```
├── agents/                         # 핵심 에이전트
│   ├── architecture_mapper.py      # 의존성 그래프 생성
│   └── impact_analyzer.py          # 변경 영향도 분석
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

## 시각화 UI

```bash
python3 -m http.server 8000
# 브라우저에서 http://localhost:8000/ui/ 접속
```

변경 시뮬레이션 버튼으로 Blast Radius가 아키텍처 그래프에서 어떻게 전파되는지 확인할 수 있습니다.

## 기술 스택

| 영역 | 기술 |
|------|------|
| 의존성 분석 | Python `ast`, 정규식 (표준 라이브러리만 사용) |
| 그래프 탐색 | BFS (표준 라이브러리 `collections.deque`) |
| 시각화 | vis-network, Tailwind CSS |
| CI/CD | GitHub Actions |
| 자동화 | Bash Shell Script (Hook) |
