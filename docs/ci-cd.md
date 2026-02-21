# CI/CD 파이프라인 연동

## GitHub Actions 워크플로우

PR이 생성되면 자동으로 영향도 분석을 수행하고 결과를 PR 코멘트로 등록합니다.

### 트리거 조건

```yaml
on:
  pull_request:
    branches: [ "main", "dev" ]
```

### 파이프라인 단계

```
Checkout ──▶ Python Setup ──▶ Install Deps ──▶ Architecture Map ──▶ Get Diff ──▶ Impact Analysis ──▶ PR Comment
```

1. **저장소 체크아웃**: `fetch-depth: 0`으로 전체 히스토리 가져옴
2. **Python 환경 설정**: Python 3.10
3. **의존성 설치**: `pip install -r agents/requirements.txt`
4. **아키텍처 맵 생성**: `architecture_mapper.py --scan-all`
5. **PR diff 추출**: `git diff origin/base...HEAD > pr_diff.patch`
6. **영향도 분석**: `impact_analyzer.py --diff pr_diff.patch`
7. **PR 코멘트**: `actions-comment-pull-request`로 리포트 자동 등록

### 설정 파일

[`.github/workflows/impact-map.yml`](../.github/workflows/impact-map.yml)

### 필요 권한

```yaml
permissions:
  pull-requests: write
  contents: read
```

## 고위험 변경 시 흐름

```
PR 생성 ──▶ Impact Analysis ──▶ 🔴 High Risk 감지
                                      │
                                      ▼
                            PR 코멘트에 경고 리포트 자동 등록
                                      │
                                      ▼
                            리뷰어가 Blast Radius 확인 후 승인/반려
```
