# 시작 가이드

## 사전 요구사항

- Python 3.10 이상
- Git

## 설치

```bash
git clone <repository-url>
cd vibe-coding-improvement-ai-idea
```

외부 라이브러리 없이 Python 표준 라이브러리만으로 동작합니다.
(확장 기능 사용 시: `pip install -r agents/requirements.txt`)

## 빠른 시작 — 데모 실행

```bash
bash examples/run_demo.sh
```

이 스크립트는 다음을 순서대로 수행합니다:
1. 예시 프로젝트(`examples/sample_project/`)의 의존성 그래프 생성
2. 특정 파일의 참조처 조회
3. 4가지 시나리오(Low/Medium/High)별 영향도 분석 리포트 출력

## 직접 사용하기

### 1단계: 아키텍처 맵 생성

```bash
# 전체 프로젝트 스캔
python3 agents/architecture_mapper.py --scan-all --root <프로젝트경로>

# 특정 파일의 의존성 조회
python3 agents/architecture_mapper.py --target src/auth.py --root <프로젝트경로>
```

### 2단계: 변경 영향도 분석

```bash
# diff 패치 파일 생성
git diff > my_changes.patch

# 영향도 분석 실행
python3 agents/impact_analyzer.py --diff my_changes.patch --map architecture_map.json
```

### 3단계: 시각화 UI 확인

```bash
python3 -m http.server 8000
# 브라우저에서 http://localhost:8000/ui/ 접속
```

## CLI 옵션 레퍼런스

### architecture_mapper.py

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--scan-all` | 전체 저장소 스캔 | - |
| `--target <파일>` | 특정 파일의 참조처 조회 | - |
| `--output <파일>` | 의존성 그래프 출력 파일 | `architecture_map.json` |
| `--root <경로>` | 프로젝트 루트 디렉토리 | `.` (현재 디렉토리) |

### impact_analyzer.py

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--diff <파일>` | diff 패치 파일 경로 | - |
| `--map <파일>` | 아키텍처 맵 JSON 파일 | `architecture_map.json` |
| `--output <파일>` | 리포트 출력 파일 (미지정 시 stdout) | stdout |

## Git Hook 활성화

```bash
# pre-commit hook 활성화
git config core.hooksPath .githooks

# 커밋 시 자동 영향도 검사가 수행됩니다
git commit -m "my changes"

# 검사 우회 (긴급 시)
git commit --no-verify -m "urgent fix"

# 환경변수로 우회
IMPACT_MAP_SKIP=1 git commit -m "skip check"
```
