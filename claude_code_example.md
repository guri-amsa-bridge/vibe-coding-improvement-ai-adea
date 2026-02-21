# Claude Code Workflow Example

Terminal 인터페이스에서 동작하는 **Claude Code**를 활용하여 Impact Map 기반 워크플로우를 진행하는 예시입니다. 이 예시는 개발자가 터미널에서 Claude Code를 켜고 어떻게 대화하며 코루틴(AI)의 안전망을 활용하는지 보여줍니다.

---

## 시나리오: 사용자 인증(Auth) 모듈 수정

### 1단계: Claude Code 실행 및 지침 전달
터미널에서 프로젝트 루트에 진입한 뒤 Claude를 실행하고 워크플로우를 주입합니다.

```bash
$ claude "AI_WORKFLOW.md 를 읽고 앞으로 모든 변경사항에 대해 해당 지침을 따라줘. 그리고 src/auth.py의 로그인 암호화 알고리즘을 SHA256에서 bcrypt로 변경해줘."
```

### 2단계: Claude Code의 아키텍처 사전 검토 (Phase 1)
Claude는 코드를 바로 수정하기 전, `agents/architecture_mapper.py`를 실행하거나 기존 의존성 맵을 파악합니다.

**(Claude Code Terminal Output 봇 응답 예시)**
> 🤖 **Claude**: `AI_WORKFLOW.md` 지침을 숙지했습니다. 
> `src/auth.py`를 변경하기 전 아키텍처 맵퍼를 실행하여 의존성을 확인하겠습니다.
> 
> ```
> RUNNING: python agents/architecture_mapper.py --target src/auth.py
> ✅ 분석결과: src/auth.py는 src/user_service.py 와 api/routes.py 에서 호출 중입니다.
> ``` 
> 암호화 로직 변경 시 `user_service.py`의 비밀번호 검증 로직도 함께 변경되어야 합니다. 수정을 진행할까요?

```bash
$ 사용자: 진행해줘.
```

### 3단계: 코드 수정 및 셀프 영향도 검증 (Phase 2 & 3)
Claude Code가 코드를 수정한 뒤, Impact Analyzer를 통해 스스로 리포트를 생성하고 요약합니다.

**(Claude Code Terminal Output 봇 응답 예시)**
> 🤖 **Claude**: `src/auth.py`와 `src/user_service.py` 수정을 완료했습니다.
> 이제 지침에 따라 `impact_analyzer.py`를 실행해 영향도를 최종 평가합니다.
> 
> ```
> RUNNING: git diff HEAD | python agents/impact_analyzer.py
> ⚠️ [IMPACT REPORT] 
> - 위험도: High
> - 확정된 영향: api/routes.py 의 Login Endpoint 파라미터 처리. 기존 구형 DB 데이터 호환성 보장 안 됨.
> - 조치 권고: DB 마이그레이션 스크립트를 추가로 작성해야 합니다.
> ```
> 변경 사항이 API 계층 구버전 로직에 충돌을 낼 수 있습니다. 추가로 마이그레이션 스크립트를 작성할까요?

---

### 요약
위와 같이 Claude Code는 터미널 컨텍스트에서 Shell 커맨드를 직접 실행할 수 있는 장점을 활용해, 코드를 짜는 중간중간 **아키텍처 스캐너와 임팩트 스캐너를 CLI 커맨드로 호출**하며 자가 검증을 수행합니다. 
이는 바이브 코딩으로 인해 발생할 수 있는 "무지향적 코드 파편화"를 막아주는 강력한 안전장치가 됩니다.
