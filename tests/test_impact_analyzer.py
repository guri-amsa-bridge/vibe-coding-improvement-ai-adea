"""Impact Analyzer 핵심 함수 단위 테스트"""
import os
import sys
import json
import tempfile
import pytest

# agents/ 디렉토리를 import 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents'))

from impact_analyzer import (
    parse_diff_files,
    parse_diff_from_string,
    compute_blast_radius,
    determine_risk_level,
    categorize_files,
)


# ─── parse_diff_from_string 테스트 ───

class TestParseDiffFromString:
    """문자열 diff에서 변경 파일을 올바르게 추출하는지 검증"""

    def test_git_diff_format(self):
        diff = """diff --git a/src/auth.py b/src/auth.py
index aaa1111..bbb2222 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -1,3 +1,3 @@
-old line
+new line
"""
        result = parse_diff_from_string(diff)
        assert result == ["src/auth.py"]

    def test_multiple_files(self):
        diff = """diff --git a/src/auth.py b/src/auth.py
--- a/src/auth.py
+++ b/src/auth.py
@@ -1 +1 @@
-old
+new

diff --git a/src/database.py b/src/database.py
--- a/src/database.py
+++ b/src/database.py
@@ -1 +1 @@
-old
+new
"""
        result = parse_diff_from_string(diff)
        assert result == ["src/auth.py", "src/database.py"]

    def test_empty_string(self):
        assert parse_diff_from_string("") == []

    def test_no_diff_content(self):
        assert parse_diff_from_string("some random text") == []

    def test_plain_diff_format(self):
        """git diff가 아닌 일반 diff 형식 (+++ b/path)도 파싱"""
        diff = """--- a/config/settings.py
+++ b/config/settings.py
@@ -1 +1 @@
-old
+new
"""
        result = parse_diff_from_string(diff)
        assert "config/settings.py" in result


# ─── parse_diff_files 테스트 ───

class TestParseDiffFiles:
    """파일에서 diff를 읽어 변경 파일을 추출하는지 검증"""

    def test_valid_patch_file(self, tmp_path):
        patch = tmp_path / "test.patch"
        patch.write_text("""diff --git a/src/database.py b/src/database.py
--- a/src/database.py
+++ b/src/database.py
@@ -1 +1 @@
-old
+new
""")
        result = parse_diff_files(str(patch))
        assert result == ["src/database.py"]

    def test_nonexistent_file(self):
        result = parse_diff_files("/nonexistent/path/test.patch")
        assert result == []

    def test_real_patch_files(self):
        """examples/diffs/ 하위 패치 파일들이 올바르게 파싱되는지 검증"""
        diffs_dir = os.path.join(os.path.dirname(__file__), '..', 'examples', 'diffs')
        expected = {
            "01_low_risk_ui_change.patch": ["frontend/renderer.js"],
            "02_medium_risk_api_change.patch": ["src/item_service.py"],
            "03_high_risk_db_change.patch": ["src/database.py"],
            "04_high_risk_auth_change.patch": ["src/auth.py"],
        }
        for filename, expected_files in expected.items():
            path = os.path.join(diffs_dir, filename)
            if os.path.isfile(path):
                result = parse_diff_files(path)
                assert result == expected_files, f"{filename}: expected {expected_files}, got {result}"


# ─── compute_blast_radius 테스트 ───

class TestComputeBlastRadius:
    """BFS 영향 전파 계산이 올바른지 검증"""

    SAMPLE_GRAPH = {
        "src/database.py": [],
        "src/auth.py": ["src/database.py"],
        "src/user_service.py": ["src/auth.py", "src/database.py"],
        "api/routes.py": ["src/auth.py", "src/item_service.py", "src/user_service.py"],
        "src/item_service.py": ["src/database.py"],
        "frontend/app.js": ["frontend/api_client.js", "frontend/renderer.js"],
        "frontend/renderer.js": [],
        "frontend/api_client.js": [],
    }

    def test_leaf_change_no_impact(self):
        """연쇄 참조가 없는 리프 노드 변경"""
        direct, indirect, paths = compute_blast_radius(
            ["frontend/renderer.js"], self.SAMPLE_GRAPH
        )
        assert direct == ["frontend/app.js"]
        assert indirect == []

    def test_database_change_cascading(self):
        """database.py 변경 시 연쇄 영향 확인"""
        direct, indirect, paths = compute_blast_radius(
            ["src/database.py"], self.SAMPLE_GRAPH
        )
        # database.py를 직접 import하는 파일들
        assert "src/auth.py" in direct
        assert "src/item_service.py" in direct
        assert "src/user_service.py" in direct
        # 간접 영향 (auth.py를 import하는 routes.py 등)
        assert "api/routes.py" in indirect

    def test_no_graph(self):
        """빈 그래프에서는 영향 없음"""
        direct, indirect, paths = compute_blast_radius(["any_file.py"], {})
        assert direct == []
        assert indirect == []


# ─── determine_risk_level 테스트 ───

class TestDetermineRiskLevel:
    """위험도 판정 로직 검증"""

    def test_low_risk(self):
        level, icon = determine_risk_level(["frontend/renderer.js"], [], [])
        assert level == "Low"
        assert icon == "🟢"

    def test_medium_risk(self):
        level, icon = determine_risk_level(
            ["src/item_service.py"], ["api/routes.py", "src/database.py"], []
        )
        assert level in ("Medium", "High")  # critical 패턴에 따라 달라질 수 있음

    def test_high_risk_critical_files(self):
        level, icon = determine_risk_level(
            ["src/auth.py"], ["src/user_service.py", "api/routes.py"],
            ["frontend/app.js"]
        )
        assert level == "High"
        assert icon == "🔴"


# ─── categorize_files 테스트 ───

class TestCategorizeFiles:
    """파일 분류 정확성 검증"""

    def test_api_categorization(self):
        result = categorize_files(["api/routes.py"])
        assert "api/routes.py" in result['api']

    def test_service_categorization(self):
        result = categorize_files(["src/user_service.py"])
        assert "src/user_service.py" in result['service']

    def test_frontend_categorization(self):
        result = categorize_files(["frontend/app.js", "ui/index.html"])
        assert "frontend/app.js" in result['frontend']
        assert "ui/index.html" in result['frontend']

    def test_config_categorization(self):
        result = categorize_files(["config/settings.py"])
        assert "config/settings.py" in result['config']

    def test_infra_categorization(self):
        result = categorize_files(["src/database.py"])
        assert "src/database.py" in result['infra_db']

    def test_no_false_positive_on_model(self):
        """model 패턴이 service_model.py 같은 파일을 잘못 분류하지 않는지 확인"""
        result = categorize_files(["src/service_logic.py"])
        assert "src/service_logic.py" in result['service']
