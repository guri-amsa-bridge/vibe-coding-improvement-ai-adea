# Impact Map: 바이브 코딩 환경을 위한 변경 영향도 자동 분석 프레임워크 데모

## 🚨 문제 정의
AI(LLM) 기반의 코딩 환경(바이브 코딩)에서는 코드 작성 속도가 비약적으로 증가하지만, **변경 코드의 영향 범위를 정확히 인지하지 못한 채 배포되는 문제**가 발생합니다. 본 프로젝트는 이 문제를 해결하기 위해 **정적 아키텍처 분석 기반 변경 영향도 맵(Impact Map) 프레임워크**를 제안하고, 어떻게 여러 AI 툴에서 일관되게 활용할 수 있는지 보여주는 데모입니다.

## 📁 프로젝트 구조

```
vibe-coding-improvement-ai-idea/
├── agents/                        # 핵심 에이전트 모듈
│   ├── architecture_mapper.py     # (Sub) 아키텍처 맵 작성 에이전트
│   ├── impact_analyzer.py         # (Main) 변경 영향도 분석 에이전트
│   └── requirements.txt           # Python 의존성
├── ui/                            # 시각화 데모 웹 UI
│   ├── index.html                 # 메인 HTML (Tailwind CSS)
│   ├── script.js                  # vis-network 기반 그래프 시각화 로직
│   └── styles.css                 # 커스텀 스타일
├── .claude/                       # Claude Code 통합
│   ├── hooks/
│   │   └── check-impact.sh        # PreToolUse Hook (Zero-Prompt 자동 방어)
│   └── skills/
│       ├── impact_map/
│       │   ├── SKILL.md            # Impact Map 분석 스킬 정의
│       │   └── template.md         # 리포트 템플릿
│       └── vibe_coding/
│           └── SKILL.md            # 바이브 코딩 공통 워크플로우 스킬
├── .githooks/
│   └── pre-commit                 # Git 프리커밋 훅 (로컬 안전장치)
├── .github/workflows/
│   └── impact-map.yml             # GitHub Actions CI/CD 파이프라인
├── .claude.json                   # Claude Code Hooks 설정
├── .cursorrules                   # Cursor 에이전트 전역 규칙
├── AI_WORKFLOW.md                 # Tool-Agnostic 공통 워크플로우 가이드
├── claude_code_example.md         # Claude Code 사용 시나리오 예시
├── architecture_map.json          # 생성된 아키텍처 의존성 맵 (JSON)
└── README.md                      # 프로젝트 문서
```

## 🔧 기술 스택

| 영역 | 기술 | 용도 |
|------|------|------|
| 에이전트 코어 | Python 3.10+ | 아키텍처 스캔 및 영향도 분석 |
| 그래프 분석 | NetworkX | 의존성 그래프 탐색·연산 |
| GitHub 연동 | PyGithub | PR Diff 수집, 코멘트 자동화 |
| LLM 추론 | OpenAI API | 변경 영향도 의미 분석 (확장용) |
| 시각화 UI | vis-network, Tailwind CSS | 아키텍처 그래프 시각화·인터랙션 |
| CI/CD | GitHub Actions | PR 기반 자동 영향도 분석·코멘트 |
| 자동화 훅 | Bash (Shell Script) | 커밋/배포 시점 자동 방어 |

## 🛠 아키텍처 (2-Agent 구조)
1. **[Architecture Mapper](./agents/architecture_mapper.py)**: 코드 저장소를 스캔하여 모듈(파일) 간 의존성을 추출하고 참조 그래프를 구축합니다.
   - `--scan-all`: 전체 저장소 스캔 → `architecture_map.json` 출력
   - `--target [파일]`: 특정 파일의 의존성 조회 (호출처·참조처 확인)
   - 출력 형식: 인접 리스트(Adjacency List) 기반 JSON 그래프
2. **[Impact Analyzer](./agents/impact_analyzer.py)**: GitHub PR이나 커밋 Diff를 확인하고, 변경된 코드가 시스템 어디에 영향을 미칠지 계산하여 리포트를 제공합니다.
   - `--diff [patch파일]`: git diff 패치 파일 입력
   - `--map [JSON파일]`: 아키텍처 맵 파일 지정 (기본값: `architecture_map.json`)
   - 출력: 위험도 등급, Blast Radius, 조치 권고 포함 리포트

## 🤖 Tool-Agnostic Workflow (AI 툴 공통 가이드)
본 프레임워크는 특정 AI 에디터에 종속되지 않습니다. 모든 AI 어시스턴트는 코드 수정 전후로 Impact Map 프로세스를 준수해야 합니다.
👉 **자세한 워크플로우는 [AI_WORKFLOW.md](./AI_WORKFLOW.md)를 참고하세요.**

### 1) Cursor 사용 시
- `.cursorrules` 파일을 통해 AI가 전역적으로 Impact Map 스킴을 이해하고 코드 제안 시 영향을 미리 고지하도록 세팅되어 있습니다.
- 개발자가 "로그인 로직 패치해줘" 라고만 해도, Cursor AI는 `.cursorrules`를 확인 후 변경 전 아키텍처를 점검합니다.

### 2) Claude Code 사용 시
- 터미널이나 CLI 기반에서 구동되는 Claude Code나 유사 툴에서는 프롬프트와 명령어 조합으로 작동합니다.
- 👉 **[claude_code_example.md](./claude_code_example.md)** 문서를 통해 구체적인 튜토리얼을 확인하세요.

### 3) 최신 Claude Code 및 Antigravity 사용 시 (Skills)
- 프레임워크 내에 구조화된 AI 스킬 디렉토리를 제공합니다. Claude Code의 기본 스킬 디렉토리 트렌드에 맞추어 `.claude/skills/` 폴더 내에 정의된 스킬들을 활용하여 에이전트들이 복잡한 변경 시 자동으로 Impact Map 스크립트를 백그라운드에서 실행하고 리포트를 생성합니다.
- 👉 **[.claude/skills/impact_map/SKILL.md](./.claude/skills/impact_map/SKILL.md)** 및 **[.claude/skills/vibe_coding/SKILL.md](./.claude/skills/vibe_coding/SKILL.md)** 문서 참조.

## 🚀 Zero-Prompt 자동화 (Hooks 통합)
본 프로젝트는 개발자가 명시적으로 분석 명령을 내리지 않아도, 2차 안전망이 백그라운드에서 동작하는 **Zero-Prompt 자동화**를 지원합니다.

### 1) Claude Code 자동 방어 시스템 (PreToolUse Hook)
Claude 내장 `Hooks` 기능을 활용해 에이전트가 자체적으로 `git commit`이나 `gh pr create` 명령(Tool)을 수행하려고 시도하면, 내부 시스템이 이를 감지하여 `.claude/hooks/check-impact.sh`를 강제 실행시킵니다.
- `High Risk` 감지 시 Claude는 권한 부족(Deny) 응답을 받고 커밋을 중단하며, 사용자 대화창에 경고를 출력합니다.
- 설정 파일: [`.claude.json`](./.claude.json) 의 PreToolUse 설정 참조.

### 2) Git Native 프리커밋(pre-commit) 안전장치
VSCode IDE 등 일반 커밋 환경에서도 개발자의 실수를 막기 위해, 로컬 Git 프리커밋 훅 체계를 내장했습니다.
- 프로젝트 저장소 복제 시 다음 명령어로 훅을 활성화할 수 있습니다.
  ```bash
  git config core.hooksPath .githooks
  ```
- 이후 커밋을 시도하면 자동으로 `agents/impact_analyzer.py`가 구동되며, 위험도가 높을 시 커밋이 차단(Exit Code 1)됩니다.
- 강제 커밋: `git commit --no-verify` (CI에서 재검증됨)

## 🚀 CI/CD 파이프라인 (GitHub Actions 연동)
개발자가 PR을 올릴 경우, 봇(봇 에이전트)이 자동으로 변경사항을 분석하여 PR 코멘트를 남깁니다.

- 워크플로우: `.github/workflows/impact-map.yml`
- 트리거: `main`, `dev` 브랜치 대상 Pull Request
- 파이프라인 단계:
  1. 저장소 체크아웃 (전체 히스토리)
  2. Python 3.10 환경 셋업 및 의존성 설치
  3. `architecture_mapper.py --scan-all` → 아키텍처 맵 생성
  4. PR Diff 추출 (`git diff origin/base...HEAD`)
  5. `impact_analyzer.py --diff --map` → Impact Report 생성
  6. PR 코멘트로 리포트 자동 등록 (`actions-comment-pull-request`)

고위험 변경사항일 경우 리뷰어의 꼼꼼한 확인을 요구하는 구조로 이어집니다.

## 🖥 시각화 데모 UI (Web Viewer)
에이전트들이 텍스트로 내뱉는 구조를 **웹 UI 그래프**로 손쉽게 시각화하여 확인해 볼 수 있습니다.

1. 터미널(Terminal)을 열고 이 프로젝트의 루트 폴더(`ui` 폴더가 있는 곳)로 이동합니다.
2. 아래 명령어를 통해 로컬 웹 서버를 실행합니다.
   ```bash
   python -m http.server 8000
   ```
3. 웹 브라우저를 열고 `http://localhost:8000/ui/` 에 접속합니다.
4. 화면 우측 상단의 **'src/auth.py' 변경 시뮬레이션** 버튼을 클릭하여 파급 효과(Blast Radius)가 아키텍처 상에 어떻게 퍼져나가는지 시각적으로 확인해볼 수 있습니다.

## 🤖 Cross-Agent 지원 (Antigravity & Cursor 연동)
Claude Code 뿐만 아니라, **Cursor** 및 **Antigravity** 에디터에서도 활용 가능하도록 연동되어 있습니다.
- **Cursor**: 루트에 위치한 `.cursorrules` 파일이 Cursor 에이전트에게 항상 `.claude/skills/**/*.md` 지침을 읽도록 유도합니다.
- **Antigravity**: 시스템이 자동으로 `.claude/skills/` 디렉토리를 인식하여 동일한 안전 검증 및 Impact Map 백그라운드 프로세스를 가이드합니다.
