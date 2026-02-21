#!/bin/bash
# =============================================================
# Impact Map 데모 실행 스크립트
# 사용법: bash examples/run_demo.sh
# =============================================================

set -e

# 프로젝트 루트 경로 설정
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SAMPLE_PROJECT="$SCRIPT_DIR/sample_project"
DIFFS_DIR="$SCRIPT_DIR/diffs"
MAPPER="$PROJECT_ROOT/agents/architecture_mapper.py"
ANALYZER="$PROJECT_ROOT/agents/impact_analyzer.py"

# Python 확인
PYTHON_CMD="python3"
if ! command -v python3 &>/dev/null; then
    PYTHON_CMD="python"
fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║       🗺️  Impact Map — 데모 실행 스크립트            ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ─────────────────────────────────────────────────
# Step 1: 아키텍처 맵 생성
# ─────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📌 Step 1: 예시 프로젝트의 아키텍처 의존성 맵 생성"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  실행: $PYTHON_CMD agents/architecture_mapper.py --scan-all --root examples/sample_project"
echo ""

$PYTHON_CMD "$MAPPER" --scan-all \
    --root "$SAMPLE_PROJECT" \
    --output "$SCRIPT_DIR/architecture_map.json"

echo ""
echo "  📄 생성된 의존성 그래프:"
cat "$SCRIPT_DIR/architecture_map.json"
echo ""
echo ""

# ─────────────────────────────────────────────────
# Step 2: 특정 파일의 의존성 조회
# ─────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📌 Step 2: 특정 파일(src/database.py)의 참조처 조회"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  실행: $PYTHON_CMD agents/architecture_mapper.py --target src/database.py"
echo ""

$PYTHON_CMD "$MAPPER" --target src/database.py --root "$SAMPLE_PROJECT"

echo ""
echo ""

# ─────────────────────────────────────────────────
# Step 3: 시나리오별 영향도 분석
# ─────────────────────────────────────────────────
DIFFS=(
    "01_low_risk_ui_change.patch|🟢 Low Risk — UI 텍스트만 변경 (renderer.js)"
    "02_medium_risk_api_change.patch|🟡 Medium Risk — 서비스 로직 변경 (item_service.py)"
    "03_high_risk_db_change.patch|🔴 High Risk — 데이터베이스 엔진 교체 (database.py)"
    "04_high_risk_auth_change.patch|🔴 High Risk — 인증 알고리즘 변경 (auth.py)"
)

STEP=3
for entry in "${DIFFS[@]}"; do
    IFS='|' read -r DIFF_FILE DESCRIPTION <<< "$entry"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📌 Step $STEP: $DESCRIPTION"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "  실행: $PYTHON_CMD agents/impact_analyzer.py --diff $DIFF_FILE --map architecture_map.json"
    echo ""

    $PYTHON_CMD "$ANALYZER" \
        --diff "$DIFFS_DIR/$DIFF_FILE" \
        --map "$SCRIPT_DIR/architecture_map.json"

    echo ""
    echo ""
    STEP=$((STEP + 1))
done

# ─────────────────────────────────────────────────
# 완료
# ─────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 데모 완료! 모든 시나리오의 영향도 분석이 수행되었습니다."
echo ""
echo "  💡 추가로 시도해볼 것:"
echo "     • Web UI 시각화: cd ui && python3 -m http.server 8080"
echo "     • 직접 diff 분석: $PYTHON_CMD agents/impact_analyzer.py --diff <your.patch> --map examples/architecture_map.json"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
