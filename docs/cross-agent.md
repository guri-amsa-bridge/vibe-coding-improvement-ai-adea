# Cross-Agent 지원

Impact Map은 특정 AI 도구에 종속되지 않는 **Tool-Agnostic 아키텍처**를 채택합니다.

## 3-Phase 공통 워크플로우

모든 AI 어시스턴트가 코드를 수정할 때 준수해야 하는 공통 프로세스입니다.

```
Phase 1                    Phase 2                    Phase 3
아키텍처 파악 ──────▶ 코드 작성 및 수정 ──────▶ 변경 영향도 자가 검증
(Pre-Check)              (Execution)              (Validation)
```

### Phase 1: 아키텍처 파악 (Pre-Check)

1. 사용자의 수정 요청 수신
2. 바로 코드를 수정하지 않고, 대상 파일의 의존성을 먼저 확인
   ```bash
   python agents/architecture_mapper.py --target <대상파일>
   ```
3. 영향받을 수 있는 파일 목록을 사용자에게 고지

### Phase 2: 코드 작성 및 수정 (Execution)

1. 파악된 영향 범위를 고려하여 코드 수정
2. 함수 시그니처나 API 인터페이스 변경 시, 함께 수정해야 할 파일을 사용자에게 안내
3. 코드 변경 확정

### Phase 3: 변경 영향도 자가 검증 (Validation)

1. 변경 사항(diff)으로 영향도 분석 실행
   ```bash
   python agents/impact_analyzer.py --diff <diff파일>
   ```
2. High Risk 시 사용자에게 즉시 경고
3. 분석 결과 요약 전달

## AI 에디터별 통합 방식

### Cursor

**설정 파일:** `.cursorrules`

Cursor의 전역 규칙 파일을 통해 AI가 코드 수정 전후로 Impact Map 프로세스를 자동 적용합니다.

- 모든 코딩 쿼리 전에 `.claude/skills/` 지침을 읽도록 유도
- 파일 수정 시 예상 영향 범위를 사용자에게 고지
- 수정 완료 후 Impact Summary를 응답 말미에 첨부

### Claude Code

**설정 파일:** `.claude.json`, `.claude/skills/`, `.claude/hooks/`

- **Skills**: `impact_map`, `vibe_coding` 스킬이 에이전트에게 분석 워크플로우를 안내
- **Hooks (PreToolUse)**: `git commit` 등 위험 명령 실행 시 자동 차단 시스템 동작
- **사용 예시**: [claude_code_example.md](./claude_code_example.md) 참조

### Antigravity 등 기타 AI 에디터

**설정 파일:** `AI_WORKFLOW.md`

- `.claude/skills/` 디렉토리를 자동 인식하는 에디터에서는 동일한 워크플로우 적용
- 그 외 에디터에서는 `AI_WORKFLOW.md`를 시스템 프롬프트에 포함하여 동일 효과 달성

## AI 프롬프트 권장 삽입문

AI 에디터의 시스템 프롬프트에 다음 문구를 추가하면 Impact Map 워크플로우가 적용됩니다:

> "당신은 코드를 작성하기 전에 반드시 이 프로젝트의 아키텍처 참조를 확인해야 합니다. 단순한 기능 추가라도 호출 체인의 붕괴를 막기 위해 AI_WORKFLOW.md의 원칙을 따라야 합니다."
