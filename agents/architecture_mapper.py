import json
import argparse
import os
import ast
import re
from collections import defaultdict


def find_source_files(root_dir, extensions=None):
    """프로젝트 디렉토리에서 소스 파일 목록을 수집한다."""
    if extensions is None:
        extensions = {'.py', '.js', '.ts', '.jsx', '.tsx'}

    skip_dirs = {
        'node_modules', '.git', '__pycache__', '.venv', 'venv',
        'env', 'dist', 'build', '.next', '.nuxt',
    }

    source_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for filename in filenames:
            ext = os.path.splitext(filename)[1]
            if ext in extensions:
                full_path = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(full_path, root_dir)
                source_files.append(rel_path)

    return source_files


def extract_python_imports(file_path):
    """Python 파일에서 AST를 이용해 import 모듈명을 추출한다."""
    imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename=file_path)
    except (SyntaxError, UnicodeDecodeError):
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return imports


def extract_js_imports(file_path):
    """JS/TS 파일에서 정규식으로 import/require 대상을 추출한다."""
    imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
    except UnicodeDecodeError:
        return imports

    # import ... from '...' 또는 import '...'
    pattern_import = re.compile(r'''import\s+.*?from\s+['"]([^'"]+)['"]''')
    # import('...')  — dynamic import
    pattern_dynamic = re.compile(r'''import\s*\(\s*['"]([^'"]+)['"]\s*\)''')
    # require('...')
    pattern_require = re.compile(r'''require\s*\(\s*['"]([^'"]+)['"]\s*\)''')

    for pattern in [pattern_import, pattern_dynamic, pattern_require]:
        imports.extend(pattern.findall(source))

    return imports


def resolve_python_import(module_name, source_files, root_dir):
    """Python 모듈명을 프로젝트 내 파일 경로로 변환한다."""
    # 모듈명의 . 을 / 로 변환
    path_candidates = [
        module_name.replace('.', '/') + '.py',
        module_name.replace('.', '/') + '/__init__.py',
    ]
    # 부분 매칭: a.b.c → a/b/c.py, a/b.py, a.py (상위 모듈도 의존성)
    parts = module_name.split('.')
    for i in range(len(parts), 0, -1):
        partial = '/'.join(parts[:i]) + '.py'
        if partial not in path_candidates:
            path_candidates.append(partial)
        partial_init = '/'.join(parts[:i]) + '/__init__.py'
        if partial_init not in path_candidates:
            path_candidates.append(partial_init)

    for candidate in path_candidates:
        if candidate in source_files:
            return candidate
    return None


def resolve_js_import(import_path, source_file, source_files, root_dir):
    """JS/TS import 경로를 프로젝트 내 파일 경로로 변환한다."""
    # node_modules 패키지는 무시
    if not import_path.startswith('.') and not import_path.startswith('/'):
        return None

    source_dir = os.path.dirname(source_file)
    resolved = os.path.normpath(os.path.join(source_dir, import_path))

    # 확장자 후보
    extensions = ['', '.js', '.ts', '.jsx', '.tsx', '/index.js', '/index.ts']
    for ext in extensions:
        candidate = resolved + ext
        if candidate in source_files:
            return candidate

    return None


def build_dependency_graph(root_dir):
    """프로젝트 전체를 스캔하여 파일 간 의존성 그래프를 구축한다."""
    source_files = find_source_files(root_dir)
    source_set = set(source_files)

    # graph[A] = [B, C] 의미: A가 B, C를 import함 (A → B, A → C)
    graph = defaultdict(list)

    for src_file in source_files:
        full_path = os.path.join(root_dir, src_file)
        ext = os.path.splitext(src_file)[1]

        deps = []
        if ext == '.py':
            imports = extract_python_imports(full_path)
            for mod in imports:
                resolved = resolve_python_import(mod, source_set, root_dir)
                if resolved and resolved != src_file:
                    deps.append(resolved)
        elif ext in {'.js', '.ts', '.jsx', '.tsx'}:
            imports = extract_js_imports(full_path)
            for imp in imports:
                resolved = resolve_js_import(imp, src_file, source_set, root_dir)
                if resolved and resolved != src_file:
                    deps.append(resolved)

        if deps:
            graph[src_file] = sorted(set(deps))

    # 의존되는 파일(참조 대상)도 노드에 포함 (빈 리스트로)
    all_deps = set()
    for deps in graph.values():
        all_deps.update(deps)
    for dep in all_deps:
        if dep not in graph:
            graph[dep] = []

    return dict(graph)


def build_reverse_graph(graph):
    """정방향 그래프에서 역방향 그래프를 구축한다.
    reverse[B] = [A] 의미: B를 import하는 파일이 A이다 (B가 변경되면 A에 영향)"""
    reverse = defaultdict(list)
    for src, deps in graph.items():
        for dep in deps:
            reverse[dep].append(src)
    return dict(reverse)


def find_dependents(target, graph):
    """target 파일을 참조(import)하는 모든 파일을 찾는다."""
    reverse = build_reverse_graph(graph)
    return sorted(reverse.get(target, []))


def main():
    parser = argparse.ArgumentParser(
        description="프로젝트 소스 코드를 스캔하여 아키텍처 의존성 맵을 생성합니다."
    )
    parser.add_argument("--scan-all", action="store_true",
                        help="전체 저장소를 스캔하여 의존성 그래프 생성")
    parser.add_argument("--target", type=str,
                        help="특정 파일을 참조하는 모듈 목록 조회")
    parser.add_argument("--output", type=str, default="architecture_map.json",
                        help="의존성 그래프 JSON 출력 파일 (기본: architecture_map.json)")
    parser.add_argument("--root", type=str, default=".",
                        help="프로젝트 루트 디렉토리 (기본: 현재 디렉토리)")
    args = parser.parse_args()

    root_dir = os.path.abspath(args.root)

    print("🔍 스캐닝 아키텍처 의존성...")
    graph = build_dependency_graph(root_dir)

    if args.target:
        target = args.target
        # 정규화: 앞의 ./ 제거
        if target.startswith('./'):
            target = target[2:]

        dependents = find_dependents(target, graph)
        direct_deps = graph.get(target, [])

        if dependents or direct_deps:
            if dependents:
                print(f"✅ 분석결과: `{target}`를 참조(import)하는 파일:")
                for dep in dependents:
                    print(f"   ← {dep}")
            if direct_deps:
                print(f"✅ 분석결과: `{target}`가 참조(import)하는 파일:")
                for dep in direct_deps:
                    print(f"   → {dep}")
            print("   => 코드를 수정하기 전에 이 의존성 파일들도 함께 수정/테스트해야 할 수 있습니다.")
        else:
            print(f"✅ 분석결과: `{target}`를 직접 참조하는 다른 핵심 모듈이 파악되지 않았습니다. "
                  "단독 수정이 비교적 안전합니다.")
        return

    # --scan-all 또는 기본 동작: 전체 그래프 출력
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=4, ensure_ascii=False)

    file_count = len(graph)
    edge_count = sum(len(deps) for deps in graph.values())
    print(f"✅ 맵 생성 완료: {args.output} (파일 {file_count}개, 의존관계 {edge_count}개)")


if __name__ == "__main__":
    main()
