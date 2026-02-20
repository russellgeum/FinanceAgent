# FinanceAgent 리팩터링 작업 목록

## 작업 그룹 1: RAG 인터페이스 정의 및 Voyage 분리

### TASK-1.1: 추상 인터페이스 정의
- **목표**: Embedding 및 VectorStore의 공통 규격 정의
- **대상 파일**:
    - `src/processors/embedder.py` (BaseEmbedder 추가)
    - `src/storage/vector_store.py` (BaseVectorStore 추가)
- **수용 기준**:
    - `BaseEmbedder`: `embed_query`, `embed_documents` 추상 메서드 포함.
    - `BaseVectorStore`: `add_documents`, `similarity_search` 추상 메서드 포함.

### TASK-1.2: Voyage 구현체 및 RAGEngine 리팩터링
- **목표**: 구체적인 구현을 인터페이스 뒤로 숨김
- **대상 파일**:
    - `src/processors/voyage_embedder.py` (신규 생성)
    - `src/agents/rag_engine.py` (리팩터링)
- **수용 기준**:
    - `RAGEngine`은 생성자에서 `BaseEmbedder`와 `BaseVectorStore` 타입을 주입받아야 함.
    - 기존 Voyage 관련 로직은 `VoyageEmbedder`로 이동.

## 작업 그룹 2: LLM 추론 엔진 추상화

### TASK-2.1: LLM 인터페이스 및 엔진 구현
- **목표**: Claude 및 Gemini 통합 관리 인터페이스 구축
- **대상 파일**:
    - `src/agents/base_llm.py` (신규 생성)
    - `src/agents/claude_engine.py` (신규 생성)
    - `src/agents/gemini_engine.py` (기존 gemini_summarizer.py 전환)
- **수용 기준**:
    - `BaseLLMEngine`: `generate(prompt: str, **kwargs) -> str` 메서드 정의.
    - 각 구현체는 API 키 관리 및 예외 처리를 캡슐화함.

### TASK-2.2: 추론 엔진 팩토리 및 서비스 통합
- **목표**: 설정에 따른 유연한 LLM 교체
- **대상 파일**:
    - `src/agents/inference_factory.py` (신규 생성)
    - `src/agents/summarizer.py` (리팩터링)
- **수용 기준**:
    - `config.py`의 설정값(LLM_PROVIDER)에 따라 `ClaudeEngine` 또는 `GeminiEngine`을 반환.
    - `summarizer.py`는 특정 API를 직접 호출하지 않고 팩토리를 사용함.

## 작업 그룹 3: 검증 및 테스트

### TASK-3.1: 단위 테스트 및 경계 검증
- **목표**: 리팩터링 후 기능 동일성 보장
- **대상 파일**: `tests/` 내 관련 파일
- **수용 기준**:
    - `scripts/check_role_boundary.sh gemini --scope all` 실행 시 통과.
    - Mock 인터페이스를 사용한 RAG 엔진 테스트 통과.
