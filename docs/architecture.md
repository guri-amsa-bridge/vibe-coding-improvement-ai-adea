# 아키텍처 설계

## 2-Agent 구조

Impact Map은 **아키텍처 스캔**과 **영향도 분석**을 분리한 2-Agent 파이프라인으로 동작합니다.

```
┌─────────────────┐       architecture_map.json       ┌─────────────────────┐
│  Architecture    │ ──────────────────────────────▶  │  Impact Analyzer     │
│  Mapper (Sub)    │                                   │  (Main)              │
│                  │                                   │                      │
│  • 소스 파일 스캔  │       git diff (patch)            │  • diff 파싱          │
│  • import 분석    │ ◀──────────────────────────────  │  • 그래프 BFS 탐색     │
│  • 의존성 그래프   │                                   │  • 위험도 판단         │
│    JSON 출력      │                                   │  • 리포트 생성         │
└─────────────────┘                                   └─────────────────────┘
```

### Architecture Mapper (`agents/architecture_mapper.py`)

프로젝트 소스 코드를 스캔하여 파일 간 의존성 그래프를 구축합니다.

**분석 방식:**
- **Python**: `ast` 모듈로 `import`, `from ... import` 구문 파싱
- **JS/TS**: 정규식으로 `import ... from`, `require()` 패턴 추출
- 모듈명을 프로젝트 내 실제 파일 경로로 매핑 (외부 패키지는 제외)

**출력 형식 — 인접 리스트 JSON:**
```json
{
    "api/routes.py": ["src/auth.py", "src/user_service.py"],
    "src/auth.py": ["src/database.py"],
    "src/database.py": []
}
```
`A: [B, C]`는 "A가 B, C를 import한다"를 의미합니다.

### Impact Analyzer (`agents/impact_analyzer.py`)

diff 파일과 아키텍처 맵을 대조하여 변경 영향 범위를 계산합니다.

**분석 파이프라인:**
1. unified diff에서 변경 파일명 추출
2. 아키텍처 맵의 **역방향 그래프** 구축 (어떤 파일이 이 파일을 import하는지)
3. **BFS**로 변경 파일에서부터 영향 전파 경로 탐색
4. 영향 노드 수 + 핵심 파일 패턴으로 위험도 동적 판단

**위험도 판단 기준:**

| 등급 | 조건 |
|------|------|
| 🟢 Low | 영향 노드 0~1개, 핵심 모듈 미포함 |
| 🟡 Medium | 영향 노드 2~3개, 또는 핵심 모듈 1개 포함 |
| 🔴 High | 영향 노드 4개 이상, 또는 핵심 모듈 포함 + 영향 2개 이상 |

**핵심 모듈 패턴:** `auth`, `security`, `database`, `config`, `api/`, `payment`, `migration`

---

## 4층 다층 방어 체계

```
┌────────────────────────────────────────────────────────┐
│  1층  AI 에디터 내부       Skills/Rules 기반 사전 인지     │
│       ─────────────────────────────────────────────── │
│  2층  커밋 시점            Claude Hook / Git Pre-commit  │
│       ─────────────────────────────────────────────── │
│  3층  PR 시점              GitHub Actions CI/CD          │
│       ─────────────────────────────────────────────── │
│  4층  리뷰 시점            시각화 UI + 리포트              │
└────────────────────────────────────────────────────────┘
```

| 층 | 방어 지점 | 메커니즘 | 파일 |
|----|----------|----------|------|
| 1층 | AI 에디터 내부 | `.cursorrules`, `.claude/skills/` | `.cursorrules`, `.claude/skills/**/*.md` |
| 2층 | 커밋 시점 | Claude Hook / Git pre-commit | `.claude/hooks/check-impact.sh`, `.githooks/pre-commit` |
| 3층 | PR 시점 | GitHub Actions | `.github/workflows/impact-map.yml` |
| 4층 | 리뷰 시점 | Web UI 시각화 | `ui/` |

---

## 데이터 흐름

```
소스 코드 ──▶ architecture_mapper.py ──▶ architecture_map.json
                                              │
git diff ──▶ impact_analyzer.py ◀─────────────┘
                    │
                    ├──▶ stdout (터미널/Hook)
                    ├──▶ PR 코멘트 (GitHub Actions)
                    └──▶ Web UI (시각화)
```
