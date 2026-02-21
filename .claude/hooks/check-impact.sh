#!/bin/bash
# .claude/hooks/check-impact.sh
# 이 스크립트는 Claude Code가 Bash 도구를 사용할 때(PreToolUse) 실행됩니다.

# Claude가 현재 실행하려는 명령어(입력)는 $1 (또는 환경변수/표준입력) 등으로 넘어올 수 있습니다.
# (Bash Tool의 command 속성에 git commit 또는 git push 등이 포함되어 있는지 내부 파싱 시뮬레이션)
# 단순 시연을 위해, 현재 변경된 파일(diff)이 있는 상황에서 무조건 검사를 수행하는 로직으로 구성합니다.

PROJECT_DIR=${CLAUDE_PROJECT_DIR:-$(pwd)}
TEMP_DIFF="$PROJECT_DIR/temp_hook_diff.patch"

# 1. 대상 명령어 확인 (여기선 단순 예시를 위해 Bash 명령에 'git commit'나 'gh pr'이 포함여부만 체크한다고 가정)
# 실제 구현시: JSON JQ로 $CLAUDE_TOOL_INPUT 파싱하여 command 추출

# 2. git diff 추출
git diff HEAD > "$TEMP_DIFF"
DIFF_SIZE=$(cat "$TEMP_DIFF" | wc -c)

if [ "$DIFF_SIZE" -lt 5 ]; then
  # 변경사항이 없거나 캡처되지 않으면 통과
  echo '{
    "hookSpecificOutput": {
      "hookEventName": "PreToolUse",
      "permissionDecision": "allow",
      "permissionDecisionReason": "No significant git diff found."
    }
  }'
  exit 0
fi

# 3. 파이썬 애널라이저 실행 
REPORT_OUT=$($PROJECT_DIR/.venv/bin/python "$PROJECT_DIR/agents/impact_analyzer.py" --diff "$TEMP_DIFF" 2>/dev/null || python3 "$PROJECT_DIR/agents/impact_analyzer.py" --diff "$TEMP_DIFF" 2>/dev/null)

rm -f "$TEMP_DIFF"

# 4. 리포트에 "High Risk"나 "High"가 포함되어 있는지 검사 (단순 텍스트 매치)
if echo "$REPORT_OUT" | grep -qi "High"; then
  # 5. 차단 결정(deny) JSON 출력
  # Claude에게 이 작업을 "거부"하도록 하여 커밋 방지
  cat <<EOF
{
  "continue": true,
  "systemMessage": "⚠️ 앗! 시스템에 거대한 파급을 미칠 수 있는 코드가 감지되었습니다. Impact Map 스캐너가 커밋을 차단했습니다.",
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Impact Analyzer detected HIGH RISK changes.\n\n$REPORT_OUT"
  }
}
EOF
else
  # 6. 통과(allow) JSON 출력
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "Impact Analysis Passed"
  }
}
EOF
fi

exit 0
