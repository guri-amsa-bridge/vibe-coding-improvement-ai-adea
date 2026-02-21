# AI_WORKFLOW.md (Impact Map Tool-Agnostic Workflow)

이 문서는 모든 AI 어시스턴트(Cursor, Claude Code, Antigravity 등)가 코드를 수정하고 제안할 때 **반드시 준수해야 하는 공통 워크플로우**입니다. 
AI는 빠른 코드 생성을 수행하지만, 동시에 자신이 만드는 변화가 미칠 '영향'을 시스템적으로 검증해야 합니다.

---

## 🛑 Phase 1: 아키텍처 파악 (Pre-Check)
1. **요구사항 수신**: 사용자가 특정 파일이나 기능의 수정을 요청합니다.
2. **의존성 확인**: 바로 코드를 수정하지 말고, 대상 파일이 어디서 호출되고 있는지 확인합니다.
   - 예시 명령어 (AI가 직접 실행 가능할 경우): `python agents/architecture_mapper.py --target [대상파일]`
   - 또는 프로젝트 루트에 있는 `architecture_map.json`을 읽고 의존성 트리를 확인합니다.

## ✍️ Phase 2: 코드 작성 및 수정 (Execution)
1. 파악된 영향 범위를 고려하여 코드를 수정합니다.
2. 함수 시그니처나 외부 파일에서 참조하는 인터페이스(API)가 변경되었다면, 어떤 파일이 함께 수정되어야 하는지 사용자에게 고지합니다.
3. 코드 변경을 확정하고 저장합니다. (or Commit)

## 🔍 Phase 3: 변경 영향도 자가 검증 (Validation)
1. **Impact Analyzer 실행**: 변경 사항(Diff)을 바탕으로 영향도 분석 스크립트를 로컬에서 실행합니다.
   - 실행 커맨드: `python agents/impact_analyzer.py --diff "git diff HEAD~1"`
2. **리포트 검토**: 스크립트가 생성한 Impact Report를 읽고, 위험 수준이 `High`(고위험)로 나오면 사용자에게 중대한 결함이나 부작용이 발생할 수 있음을 경고합니다.
3. **사용자 컨펌**: 분석 결과를 요약하여 개발자에게 전달한 뒤 다음 작업으로 넘어갑니다.

---

### AI 프롬프트 필수 포함 권장 사항 (System Prompt Insert)
> "당신은 코드를 작성하기 전에 반드시 이 프로젝트의 아키텍처 참조를 확인해야 합니다. 단순한 기능 추가라도 호출 체인의 붕괴를 막기 위해 Impact Map(AI_WORKFLOW.md)의 원칙을 따라야 합니다."
