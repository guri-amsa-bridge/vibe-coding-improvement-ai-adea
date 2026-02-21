# Hook 기반 자동 방어 시스템

개발자가 별도 명령 없이도 커밋/배포 시점에 자동으로 영향도 검사가 수행됩니다.

## Claude Code PreToolUse Hook

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
