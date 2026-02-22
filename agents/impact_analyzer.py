import sys
import argparse
import json
import re
import os
from collections import deque

# 공유 유틸리티 함수를 architecture_mapper에서 가져옴
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from architecture_mapper import build_reverse_graph


def parse_diff_files(diff_path):
    """unified diff 파일에서 변경된 파일 경로 목록을 추출한다."""
    changed_files = set()

    try:
        with open(diff_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except (FileNotFoundError, PermissionError, OSError, UnicodeDecodeError) as e:
        print(f"⚠️  diff 파일 읽기 실패: {diff_path} ({type(e).__name__}: {e})", file=sys.stderr)
        return list(changed_files)

    # git diff 형식: diff --git a/path b/path
    for match in re.finditer(r'^diff --git a/(.+?) b/(.+?)$', content, re.MULTILINE):
        changed_files.add(match.group(2))

    # --- a/path, +++ b/path 형식 (git diff가 아닌 일반 diff 대응)
    for match in re.finditer(r'^\+\+\+ b/(.+?)$', content, re.MULTILINE):
        path = match.group(1)
        if path != '/dev/null':
            changed_files.add(path)

    return sorted(changed_files)


def parse_diff_from_string(diff_string):
    """문자열로 받은 diff에서 변경된 파일 경로 목록을 추출한다."""
    changed_files = set()

    for match in re.finditer(r'^diff --git a/(.+?) b/(.+?)$', diff_string, re.MULTILINE):
        changed_files.add(match.group(2))

    for match in re.finditer(r'^\+\+\+ b/(.+?)$', diff_string, re.MULTILINE):
        path = match.group(1)
        if path != '/dev/null':
            changed_files.add(path)

    return sorted(changed_files)


def load_architecture_map(map_path):
    """architecture_map.json을 로드한다."""
    try:
        with open(map_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  아키텍처 맵 파일을 찾을 수 없습니다: {map_path}", file=sys.stderr)
        return {}
    except json.JSONDecodeError as e:
        print(f"⚠️  아키텍처 맵 JSON 파싱 오류: {map_path} ({e})", file=sys.stderr)
        return {}




def compute_blast_radius(changed_files, graph):
    """변경된 파일로부터 BFS로 영향 전파 경로를 계산한다.

    Returns:
        direct_impact: 변경 파일을 직접 import하는 파일들
        indirect_impact: 연쇄적으로 영향받는 파일들
        impact_paths: 영향 전파 경로 (파일 → 경로)
    """
    reverse = build_reverse_graph(graph)

    direct_impact = set()
    indirect_impact = set()
    impact_paths = {}
    visited = set(changed_files)

    # BFS: 변경 파일 → 직접 참조처 → 연쇄 참조처
    queue = deque()

    for cf in changed_files:
        dependents = reverse.get(cf, [])
        for dep in dependents:
            if dep not in visited and dep not in changed_files:
                direct_impact.add(dep)
                visited.add(dep)
                queue.append((dep, [cf, dep]))
                impact_paths[dep] = [cf, dep]

    # 2단계 이상: 간접 영향
    while queue:
        current, path = queue.popleft()
        dependents = reverse.get(current, [])
        for dep in dependents:
            if dep not in visited and dep not in changed_files:
                indirect_impact.add(dep)
                visited.add(dep)
                new_path = path + [dep]
                queue.append((dep, new_path))
                impact_paths[dep] = new_path

    return sorted(direct_impact), sorted(indirect_impact), impact_paths


def categorize_files(files):
    """파일 경로를 계층별로 분류한다."""
    categories = {
        'api': [],
        'service': [],
        'infra_db': [],
        'frontend': [],
        'config': [],
        'other': [],
    }

    api_patterns = ['api/', 'routes/', 'endpoint', 'controller', 'handler']
    service_patterns = ['service', 'usecase', 'logic', 'auth']
    infra_patterns = ['database', 'db/', 'migration', 'models/', 'model.py', 'schema', 'infra/', 'deploy']
    frontend_patterns = ['frontend/', 'ui/', 'component', 'view', 'page', '.html', '.jsx', '.tsx']
    config_patterns = ['config/', 'config.py', '.env', 'setting', '.yml', '.yaml', '.toml']

    for f in files:
        f_lower = f.lower()
        if any(p in f_lower for p in api_patterns):
            categories['api'].append(f)
        elif any(p in f_lower for p in service_patterns):
            categories['service'].append(f)
        elif any(p in f_lower for p in infra_patterns):
            categories['infra_db'].append(f)
        elif any(p in f_lower for p in frontend_patterns):
            categories['frontend'].append(f)
        elif any(p in f_lower for p in config_patterns):
            categories['config'].append(f)
        else:
            categories['other'].append(f)

    return categories


def determine_risk_level(changed_files, direct_impact, indirect_impact):
    """영향 범위에 따라 위험도를 동적으로 결정한다."""
    total_impacted = len(direct_impact) + len(indirect_impact)
    all_affected = changed_files + direct_impact + indirect_impact

    # 핵심 파일 패턴 (이 파일이 포함되면 위험도 상승)
    critical_patterns = ['auth', 'security', 'database', 'config', 'api/', 'payment', 'migration']
    has_critical = any(
        any(p in f.lower() for p in critical_patterns)
        for f in all_affected
    )

    if total_impacted >= 4 or (total_impacted >= 2 and has_critical):
        return 'High', '🔴'
    elif total_impacted >= 2 or (total_impacted >= 1 and has_critical):
        return 'Medium', '🟡'
    else:
        return 'Low', '🟢'


def generate_recommendations(risk_level, categories, changed_files):
    """위험도와 영향 범위에 따라 조치 권고사항을 생성한다."""
    recommendations = []

    if categories['infra_db']:
        recommendations.append("DB 스키마 관련 변경이 감지되었습니다. 마이그레이션 스크립트를 확인하세요.")
    if categories['api']:
        recommendations.append("API 계층 변경이 감지되었습니다. API 컨트랙트 하위호환성을 확인하세요.")
    if categories['frontend']:
        recommendations.append("프론트엔드에 영향이 있습니다. UI 회귀 테스트를 수행하세요.")
    if categories['config']:
        recommendations.append("설정 파일 변경이 포함됩니다. 환경변수 및 배포 설정을 재확인하세요.")

    if risk_level == 'High':
        recommendations.append("통합 테스트(Integration Test)를 반드시 수행하세요.")
        recommendations.append("PR 반영 전 시니어 리뷰어의 승인을 받으세요.")
    elif risk_level == 'Medium':
        recommendations.append("관련 모듈의 단위 테스트를 실행하세요.")
    else:
        recommendations.append("자동 병합이 가능한 수준입니다.")

    if not recommendations:
        recommendations.append("특별한 조치사항이 없습니다.")

    return recommendations


def generate_report(changed_files, direct_impact, indirect_impact, impact_paths,
                    risk_level, risk_icon, categories, recommendations):
    """Impact Report를 생성한다."""
    total_impacted = len(direct_impact) + len(indirect_impact)

    review_msg = {
        'High': '이번 변경은 배포 전 반드시 통합 테스트(Integration Test)를 거쳐야 합니다.',
        'Medium': '관련 모듈의 단위 테스트를 권장합니다.',
        'Low': '자동 병합 가능한 수준입니다. 일반 리뷰를 진행하세요.',
    }

    report_lines = [
        "# ⚠️ [IMPACT REPORT] 변경 영향도 분석 리포트",
        "",
        "> **코드 파편화 자동 방어 시스템 (Impact Map)** 이 실행되었습니다. "
        "변경 사항이 시스템 전체에 미치는 파급 효과를 측정한 결과입니다.",
        "",
        "## 📊 Summary",
        f"- **변경 파일 수**: {len(changed_files)}개",
        f"- **영향받는 파일 수**: {total_impacted}개 "
        f"(직접 {len(direct_impact)}개 + 간접 {len(indirect_impact)}개)",
        f"- **전체 위험도**: {risk_icon} {risk_level}",
        f"- **리뷰 권장 사항**: {review_msg.get(risk_level, '')}",
        "",
        "## 📁 변경된 파일",
    ]

    for f in changed_files:
        report_lines.append(f"- `{f}`")

    if direct_impact or indirect_impact:
        report_lines.append("")
        report_lines.append("## 🛠 확정된 영향 범위 (Confirmed Blast Radius)")

        if categories['api']:
            report_lines.append(
                f"1. **API 계층**: {', '.join(f'`{f}`' for f in categories['api'])}"
            )
        if categories['service']:
            report_lines.append(
                f"2. **서비스 계층**: {', '.join(f'`{f}`' for f in categories['service'])}"
            )
        if categories['infra_db']:
            report_lines.append(
                f"3. **인프라/DB 계층**: {', '.join(f'`{f}`' for f in categories['infra_db'])}"
            )
        if categories['frontend']:
            report_lines.append(
                f"4. **프론트엔드 계층**: {', '.join(f'`{f}`' for f in categories['frontend'])}"
            )
        if categories['config']:
            report_lines.append(
                f"5. **설정 계층**: {', '.join(f'`{f}`' for f in categories['config'])}"
            )
        if categories['other']:
            report_lines.append(
                f"6. **기타**: {', '.join(f'`{f}`' for f in categories['other'])}"
            )

        # 영향 전파 경로
        if impact_paths:
            report_lines.append("")
            report_lines.append("## 🔗 영향 전파 경로 (Impact Paths)")
            for target, path in sorted(impact_paths.items()):
                report_lines.append(f"- {' → '.join(f'`{p}`' for p in path)}")

    report_lines.append("")
    report_lines.append("## 💡 에이전트 조치 권고 (Recommended Action)")
    for rec in recommendations:
        report_lines.append(f"- {rec}")

    return '\n'.join(report_lines)


def main():
    parser = argparse.ArgumentParser(
        description="변경 diff를 아키텍처 맵과 대조하여 영향 범위를 분석합니다."
    )
    parser.add_argument("--diff", type=str,
                        help="diff 패치 파일 경로")
    parser.add_argument("--map", type=str, default="architecture_map.json",
                        help="아키텍처 맵 JSON 파일 (기본: architecture_map.json)")
    parser.add_argument("--output", type=str, default=None,
                        help="리포트 출력 파일 (미지정 시 stdout)")
    args, unknown = parser.parse_known_args()

    # 1. diff에서 변경 파일 추출
    changed_files = []
    if args.diff:
        if os.path.isfile(args.diff):
            changed_files = parse_diff_files(args.diff)
        else:
            # 파일이 아닌 경우 문자열로 처리 시도
            changed_files = parse_diff_from_string(args.diff)

    if not changed_files:
        report = ("# ✅ [IMPACT REPORT] 변경 영향도 분석 리포트\n\n"
                  "> 분석 가능한 변경사항이 없습니다.\n\n"
                  "## 📊 Summary\n"
                  "- **전체 위험도**: 🟢 Low\n"
                  "- **변경 파일 수**: 0개\n")
        print(report)
        return

    # 2. 아키텍처 맵 로드
    print("🧠 Impact Analyzer 분석 중... 변경점과 아키텍처 맵(Graph) 대조", file=sys.stderr)
    graph = load_architecture_map(args.map)

    # 3. 영향 범위 계산 (BFS)
    direct_impact, indirect_impact, impact_paths = compute_blast_radius(
        changed_files, graph
    )

    # 4. 위험도 판단
    risk_level, risk_icon = determine_risk_level(
        changed_files, direct_impact, indirect_impact
    )

    # 5. 영향받는 파일 분류
    all_impacted = direct_impact + indirect_impact
    categories = categorize_files(all_impacted)

    # 6. 권고사항 생성
    recommendations = generate_recommendations(risk_level, categories, changed_files)

    # 7. 리포트 생성
    report = generate_report(
        changed_files, direct_impact, indirect_impact, impact_paths,
        risk_level, risk_icon, categories, recommendations
    )

    # 8. 출력
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 리포트 저장 완료: {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
