"""Architecture Mapper 핵심 함수 단위 테스트"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents'))

from architecture_mapper import (
    build_reverse_graph,
    resolve_python_import,
    find_source_files,
)


class TestBuildReverseGraph:
    """역방향 그래프 구축 검증"""

    def test_simple_graph(self):
        graph = {
            "a.py": ["b.py", "c.py"],
            "b.py": ["c.py"],
            "c.py": [],
        }
        reverse = build_reverse_graph(graph)
        assert sorted(reverse["c.py"]) == ["a.py", "b.py"]
        assert reverse["b.py"] == ["a.py"]
        assert "a.py" not in reverse

    def test_empty_graph(self):
        assert build_reverse_graph({}) == {}

    def test_single_dependency(self):
        graph = {"main.py": ["utils.py"], "utils.py": []}
        reverse = build_reverse_graph(graph)
        assert reverse["utils.py"] == ["main.py"]


class TestResolvePythonImport:
    """Python import 모듈명 → 파일 경로 변환 검증"""

    def test_simple_module(self):
        source_files = {"database.py", "auth.py", "utils.py"}
        result = resolve_python_import("database", source_files, ".")
        assert result == "database.py"

    def test_dotted_module(self):
        source_files = {"src/auth.py", "src/database.py"}
        result = resolve_python_import("src.auth", source_files, ".")
        assert result == "src/auth.py"

    def test_unknown_module(self):
        source_files = {"main.py"}
        result = resolve_python_import("nonexistent", source_files, ".")
        assert result is None

    def test_stdlib_module(self):
        """표준 라이브러리 모듈은 프로젝트 내 파일로 매칭되지 않아야 함"""
        source_files = {"main.py", "utils.py"}
        result = resolve_python_import("os", source_files, ".")
        assert result is None


class TestFindSourceFiles:
    """소스 파일 탐색 검증"""

    def test_sample_project(self):
        sample_dir = os.path.join(
            os.path.dirname(__file__), '..', 'examples', 'sample_project'
        )
        if os.path.isdir(sample_dir):
            files = find_source_files(sample_dir)
            assert len(files) > 0
            # Python과 JS 파일이 포함되어야 함
            extensions = {os.path.splitext(f)[1] for f in files}
            assert '.py' in extensions
            assert '.js' in extensions
