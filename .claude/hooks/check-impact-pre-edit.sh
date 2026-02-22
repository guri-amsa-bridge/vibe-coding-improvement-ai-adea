#!/bin/bash
# .claude/hooks/check-impact-pre-edit.sh
# ───────────────────────────────────────────────────────────────
# 0층 방어: AI가 파일을 수정(Edit/Write)하기 직전에 실행되는 Hook.
# 수정 대상 파일의 의존성을 분석하여, 영향 범위가 클 경우
# Claude에게 경고 메시지를 전달하고 수정을 차단합니다.
# ───────────────────────────────────────────────────────────────

# IMPACT_MAP_SKIP=1 환경변수로 검사 우회 가능 (개발 중 사용)
if [ "$IMPACT_MAP_SKIP" = "1" ]; then
  exit 0
fi

PROJECT_DIR=${CLAUDE_PROJECT_DIR:-$(pwd)}

# ──────────────────────────────────────
# 1. stdin에서 tool_input JSON 파싱
# ──────────────────────────────────────
# Claude Code는 PreToolUse Hook 실행 시 stdin으로 JSON을 전달합니다.
# JSON에는 tool_name, tool_input(file_path 등)이 포함됩니다.
INPUT=$(cat)

# file_path 추출 (Edit, Write 도구 모두 file_path 키를 사용)
# jq가 없는 환경을 위해 grep/sed 기반 파싱도 fallback
if command -v jq &>/dev/null; then
  FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
else
  # jq가 없는 경우 정규식으로 추출
  FILE_PATH=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*:.*"\(.*\)"/\1/')
fi

# 파일 경로를 추출할 수 없으면 통과
if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# ──────────────────────────────────────
# 2. 상대 경로로 변환
# ──────────────────────────────────────
# 절대 경로가 들어올 경우 프로젝트 루트 기준 상대 경로로 변환
REL_PATH="$FILE_PATH"
if [[ "$FILE_PATH" == /* ]] || [[ "$FILE_PATH" == *:* ]]; then
  # 절대 경로인 경우 프로젝트 루트 기준 상대 경로로 변환 시도
  REL_PATH=$(python3 -c "import os; print(os.path.relpath('$FILE_PATH', '$PROJECT_DIR'))" 2>/dev/null || echo "$FILE_PATH")
fi

# 역슬래시를 슬래시로 변환 (Windows 호환)
REL_PATH=$(echo "$REL_PATH" | sed 's|\\|/|g')

# ──────────────────────────────────────
# 3. 검사 대상 필터링
# ──────────────────────────────────────
# 소스 코드 파일만 분석 (설정 파일, 문서 등은 건너뛰기)
EXTENSION="${REL_PATH##*.}"
case "$EXTENSION" in
  py|js|ts|jsx|tsx)
    # 소스 코드 파일 → 분석 진행
    ;;
  *)
    # 소스 코드가 아닌 파일 → 무조건 통과
    exit 0
    ;;
esac

# 테스트 파일은 제외
if echo "$REL_PATH" | grep -qiE "(test_|_test\.|spec\.|\.test\.)"; then
  exit 0
fi

# ──────────────────────────────────────
# 4. 아키텍처 맵 기반 의존성 분석
# ──────────────────────────────────────
# architecture_mapper.py를 실행하여 영향받는 파일 목록을 추출
MAPPER_SCRIPT="$PROJECT_DIR/agents/architecture_mapper.py"

if [ ! -f "$MAPPER_SCRIPT" ]; then
  # 매퍼 스크립트가 없으면 통과
  exit 0
fi

# --target 모드로 의존성 조회
ANALYSIS_OUTPUT=$(python3 "$MAPPER_SCRIPT" --target "$REL_PATH" --root "$PROJECT_DIR" 2>/dev/null)

# ──────────────────────────────────────
# 5. 영향 범위 판정
# ──────────────────────────────────────
# "참조(import)하는 파일" 줄의 개수로 영향도 측정
DEPENDENT_COUNT=$(echo "$ANALYSIS_OUTPUT" | grep -c "←" 2>/dev/null || echo "0")
DEPENDENCY_COUNT=$(echo "$ANALYSIS_OUTPUT" | grep -c "→" 2>/dev/null || echo "0")
TOTAL_IMPACT=$((DEPENDENT_COUNT + DEPENDENCY_COUNT))

# 핵심 모듈 패턴 매칭
CRITICAL_PATTERNS="auth|security|database|config|payment|migration"
IS_CRITICAL=0
if echo "$REL_PATH" | grep -qiE "$CRITICAL_PATTERNS"; then
  IS_CRITICAL=1
fi

# ──────────────────────────────────────
# 6. 위험도 판정 및 결과 반환
# ──────────────────────────────────────
# 위험도 판정:
#   High:   참조 파일 3개 이상 OR (핵심 모듈 AND 참조 파일 2개 이상)
#   Medium: 참조 파일 2개 이상 OR 핵심 모듈
#   Low:    그 외

if [ "$DEPENDENT_COUNT" -ge 3 ] || ([ "$IS_CRITICAL" -eq 1 ] && [ "$DEPENDENT_COUNT" -ge 2 ]); then
  # 🔴 High Risk → 수정 차단, Claude에게 경고 전달
  IMPACT_FILES=$(echo "$ANALYSIS_OUTPUT" | grep "←" | sed 's/.*← //' | tr '\n' ', ' | sed 's/,$//')

  cat >&2 <<EOF

⚠️ [Impact Map 0층 방어] 고위험 변경 감지!

📁 수정 대상: ${REL_PATH}
🔴 위험도: High
📊 이 파일을 참조하는 모듈 ${DEPENDENT_COUNT}개 발견

🛠 영향받는 파일:
$(echo "$ANALYSIS_OUTPUT" | grep "←")

💡 이 파일을 수정하면 위 ${DEPENDENT_COUNT}개 파일에 영향을 줄 수 있습니다.

👤 사용자에게 다음과 같이 확인을 요청하세요:
"${REL_PATH} 파일을 수정하면 ${IMPACT_FILES} 등 ${DEPENDENT_COUNT}개 파일에 영향을 줄 수 있습니다. 
계속 수정하시겠습니까? 수정을 원하시면 말씀해 주세요."

EOF
  exit 2

elif [ "$DEPENDENT_COUNT" -ge 2 ] || [ "$IS_CRITICAL" -eq 1 ]; then
  # 🟡 Medium Risk → 수정은 허용하되, Claude에게 주의 메시지 전달
  echo '{"decision":"allow","suppressOutput":false}' > /dev/null

  cat >&2 <<EOF

ℹ️ [Impact Map 0층 방어] 중간 위험도 변경 감지

📁 수정 대상: ${REL_PATH}
🟡 위험도: Medium
📊 이 파일을 참조하는 모듈 ${DEPENDENT_COUNT}개 발견

$(echo "$ANALYSIS_OUTPUT" | grep -E "←|→")

💡 수정을 진행하되, 위 파일들에 대한 영향을 함께 고려해 주세요.

EOF
  # Medium은 차단하지 않고 경고만 (exit 0으로 허용)
  exit 0

else
  # 🟢 Low Risk → 통과
  exit 0
fi
