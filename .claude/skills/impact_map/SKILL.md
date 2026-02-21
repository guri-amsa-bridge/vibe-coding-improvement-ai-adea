---
name: impact_map
description: 변경 파급 효과(Impact Map)를 분석하고 시스템 아키텍처 스캔 및 영향을 자가 검증하기 위한 스킬
allowed-tools: Bash, Read, Grep
---
# /impact-map


이 스킬은 AI 봇(Claude Code 등)이 코드를 수정하거나 기능 개발 지시(Task)를 받았을 때 자동으로 로드하고 따라야 하는 명령어 집합입니다.

## 지침 (Instructions)

1. **사용자 요청 분석 시점**에, 대규모 리팩토링이나 코어 로직 수정을 요구받는다면 `vibe_coding` 스킬에 정의된 가이드를 우선 숙지하십시오.
2. 작업을 시작하기 전, 수정 대상 파일들의 의존성을 파악하기 위해 터미널에서 `python agents/architecture_mapper.py --target [파일경로들]`을 실행하세요.
3. 실행 결과를 바탕으로 작업 계획을 수립할 때, **[Impact Analysis]** 섹션을 추가하여 변경 사항이 데이터베이스, 외부 API, 또는 다른 모듈에 미칠 영향을 서술하세요.
4. 작업이 끝나고 코드를 수정한 뒤, 변경된 Diff를 기반으로 `python agents/impact_analyzer.py` 스크립트를 실행하여 안전성을 검증하세요. 검증에 실패하거나 `High Risk`로 판단될 경우, 코드 수정을 재고하고 사용자에게 즉시 알리십시오.

## 터미널 명령어 활용 예
- 아키텍처 의존성 추출: `python agents/architecture_mapper.py --scan-all`
- 특정 타겟 스캔: `python agents/architecture_mapper.py --target src/auth.py`
- 변경 영향도 리포트 생성 및 확인: `git diff HEAD > temp_diff.patch && python agents/impact_analyzer.py --diff temp_diff.patch`
