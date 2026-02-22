# Hook 기반 자동 방어 시스템

개발자가 별도 명령 없이도 코드 수정/커밋/배포 시점에 자동으로 영향도 검사가 수행됩니다.

## 0층 방어: Pre-Edit Hook (코드 수정 직전 차단)

AI가 파일을 수정하려는 **바로 그 순간**, 수정 대상 파일의 의존성을 분석하여 영향 범위가 클 경우 수정을 차단하고 개발자에게 확인을 요청합니다.

**설정 파일:** `.claude.json`
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-impact-pre-edit.sh"
      }]
    }]
  }
}
```

**동작 흐름:**
1. Claude가 Edit 또는 Write 도구 호출 시도 (파일 수정/생성)
2. `check-impact-pre-edit.sh`가 자동 실행
3. stdin의 JSON에서 수정 대상 파일 경로 추출
4. `architecture_mapper.py --target <파일>` 실행하여 의존성 분석
5. 위험도 판정:
   - 🔴 High Risk → `exit 2` (수정 차단) + 영향 범위를 Claude에게 전달
   - 🟡 Medium Risk → 경고 메시지 전달 + 수정 허용
   - 🟢 Low Risk → 무조건 통과

**스크립트:** `.claude/hooks/check-impact-pre-edit.sh`

**예시 (High Risk 차단 시 Claude가 사용자에게 전달하는 메시지):**
```
⚠️ src/auth.py를 수정하면 user_service.py, routes.py 등 3개 파일에 영향을 줄 수 있습니다.
계속 수정하시겠습니까?
```

---

## 2층 방어: Claude Code PreToolUse Hook (커밋 시점 차단)

Claude Code가 Bash 도구로 `git commit`, `gh pr create` 등을 실행하려 할 때 시스템이 자동 인터셉트합니다.

**설정 파일:** `.claude.json`
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-impact.sh"
      }]
    }]
  }
}
```

**동작 흐름:**
1. Claude가 Bash 도구 호출 시도
2. `check-impact.sh`가 자동 실행
3. `git diff HEAD` 추출 → `impact_analyzer.py` 실행
4. 🔴 High Risk 감지 시 → `permissionDecision: "deny"` 반환 → 명령 차단
5. 🟢 Low/Medium → `permissionDecision: "allow"` 반환 → 명령 진행

**스크립트:** `.claude/hooks/check-impact.sh`

## Git Pre-commit Hook

IDE나 터미널에서 직접 커밋할 때 자동 검사합니다.

**활성화:**
```bash
git config core.hooksPath .githooks
```

**동작 흐름:**
1. `git commit` 실행
2. `.githooks/pre-commit` 자동 실행
3. `git diff --cached` (staged 변경사항) 추출
4. `impact_analyzer.py` 실행
5. 🔴 High Risk → `exit 1` (커밋 차단)
6. 🟢 Low/Medium → `exit 0` (커밋 허용)

**강제 커밋:**
```bash
git commit --no-verify -m "urgent fix"
```

## 검사 우회 (개발 중)

두 Hook 모두 환경변수로 우회 가능합니다:
```bash
IMPACT_MAP_SKIP=1 git commit -m "skip check"
```

이는 개발 중 반복 커밋 시 유용하며, CI/CD에서 재검증되므로 최종 안전망은 유지됩니다.
