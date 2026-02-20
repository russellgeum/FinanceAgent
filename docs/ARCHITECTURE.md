# FinanceAgent 리팩터링 아키텍처: RAG 및 LLM 추론 엔진 추상화

## 1. 문제 정의
현재 FinanceAgent는 특정 제공자(Voyage AI, Google Gemini, Anthropic Claude)에 대한 의존성이 코드 전반에 결합되어 있어, 새로운 엔진 도입이나 교체가 어렵고 테스트 용이성이 낮음.

## 2. 시스템 경계 및 컴포넌트 구조
시스템을 **추상 인터페이스 레이어(Abstract Layer)**와 **구현 레이어(Implementation Layer)**로 분리한다.

### 2.1 RAG 엔진 컴포넌트 (Embedding + VectorStore)
- **BaseEmbedder (Interface)**: 텍스트를 벡터로 변환하는 추상 인터페이스.
- **BaseVectorStore (Interface)**: 벡터 검색 및 저장을 담당하는 추상 인터페이스.
- **VoyageEmbedder (Implementation)**: Voyage AI API를 사용한 `BaseEmbedder` 구현체.
- **ChromaVectorStore (Implementation)**: ChromaDB를 사용한 `BaseVectorStore` 구현체.
- **RAGEngine**: 추상화된 `Embedder`와 `VectorStore`를 주입받아 검색-생성 흐름을 제어하는 오케스트레이터.

### 2.2 LLM 추론 엔진 컴포넌트
- **BaseLLMEngine (Interface)**: 다양한 LLM 제공자를 통합 관리하는 추상 인터페이스.
- **ClaudeEngine (Implementation)**: Anthropic API용 구현체.
- **GeminiEngine (Implementation)**: Google Generative AI API용 구현체.
- **InferenceFactory**: 설정에 따라 적절한 `BaseLLMEngine` 구현체를 반환하는 팩토리.

## 3. 데이터 흐름
1. **색인**: `Document` -> `BaseEmbedder` -> `Vector(List[float])` -> `BaseVectorStore.add()`.
2. **검색**: `Query` -> `BaseEmbedder` -> `Query Vector` -> `BaseVectorStore.search()` -> `Context`.
3. **추론**: `Query + Context` -> `InferenceFactory` -> `BaseLLMEngine.generate()` -> `Response`.

## 4. 리스크 및 롤아웃 전략
- **리스크**: 추상화 도입으로 인한 초기 복잡도 증가.
- **전략**: 기존 기능을 유지한 상태에서 인터페이스를 먼저 정의하고, 점진적으로 구현체를 분리하여 교체 테스트를 수행한다.
