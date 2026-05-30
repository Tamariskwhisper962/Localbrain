# Ollama 의존성 제거 방법

## 왜 빼고 싶은가
Ollama는 **별도 설치·상시 실행이 필요한 외부 프로세스(데몬)**다. 배포용 범용 도구가
"먼저 Ollama 깔고 켜세요"를 요구하면 마찰이 크다. 목표: **외부 데몬 없이 임베딩 생성.**

## 결정적 전제 — 우리는 "생성 LLM"이 필요 없다 ★
MCP 구조에서 **생성·추론은 Claude(클라이언트)**가 한다 (index.html §06 참조).
localbrain이 로컬에서 돌려야 하는 건 오직 **임베딩(인코더) 모델** 하나뿐이다.
인코더는 작고(수십~수백 MB) **인프로세스 실행이 쉬워서**, Ollama를 빼는 게 깔끔하다.
- 클러스터링(축 D)도 모델 불필요 — 임베딩 벡터 + HDBSCAN(순수 수학).
- 군집 "이름 붙이기"가 필요하면 Claude에게 시키면 됨 → 역시 로컬 생성 LLM 불필요.

## 옵션 비교

| 옵션 | 데몬? | 무게 | 한국어 | 비고 |
|------|:---:|------|:---:|------|
| **fastembed (ONNX)** ⭐ | ❌ | 가벼움(토치 없음) | ◎ (multilingual-e5, bge-m3 지원) | Qdrant 제작. CPU 빠름, 번들 쉬움 |
| sentence-transformers | ❌ | 무거움(PyTorch ~GB) | ◎ | 모델 최다, GPU 가속 |
| llama.cpp (GGUF, in-proc) | ❌ | 중간 | ◎ (bge-m3 GGUF) | Ollama가 쓰는 그 엔진을 직접 임베드 |
| **Ollama** (현행) | ✅ | — | ◎ | 외부 설치·실행 필요 ← 제거 대상 |
| 클라우드 임베딩 API | ❌(네트워크) | — | ◎ | 데이터 외부 전송 → 로컬·프라이버시 훼손, 비추천 |

## 권고 — `fastembed` (인프로세스 ONNX)
- **외부 데몬 0, 완전 오프라인, PyTorch 불필요, CPU에서 빠름**, 모델 파일 캐시/번들 용이.
- multilingual-e5·bge 계열 등 한국어 가능한 모델 제공.
- Atlas의 .NET 변형이라면 동일 사상으로 `Microsoft.ML.OnnxRuntime` + ONNX 임베딩 모델.

### Provider 추상화 — 교체를 1급으로

모델 교체를 "쉽게, 반복적으로" 하려면 임베딩을 **Provider 인터페이스** 뒤로 숨긴다.
교체는 **config 한 줄**, 코드 변경 0. (재인덱싱 워크플로우는 [`architecture.md`](architecture.md) §9)

```python
# core/embed.py — 공통 인터페이스
from typing import Protocol
class EmbeddingProvider(Protocol):
    model_id: str          # 예: "fastembed:multilingual-e5-large"
    dim: int               # 벡터 차원 (컬렉션 버전 키)
    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...

# 구현체 예: 인프로세스 ONNX (데몬 없음)
class FastEmbedProvider:
    def __init__(self, name="intfloat/multilingual-e5-large"):
        from fastembed import TextEmbedding
        self._m = TextEmbedding(name)        # 최초 1회 다운로드→캐시
        self.model_id, self.dim = f"fastembed:{name}", 1024
    def embed_texts(self, texts):
        return [v.tolist() for v in self._m.embed(texts)]

# 레지스트리 — config에서 선택
PROVIDERS = {
    "fastembed": FastEmbedProvider,            # 권장(데몬 없음)
    "sentence-transformers": STProvider,       # 모델 최다
    "ollama": OllamaProvider,                  # 외부 데몬
    "onnx": OnnxProvider, "cloud": CloudProvider,
}
def make_provider(cfg) -> EmbeddingProvider:
    return PROVIDERS[cfg["provider"]](cfg["model"])
```

```yaml
# config.yaml — 교체는 여기 두 줄만
embedding:
  provider: fastembed
  model: intfloat/multilingual-e5-large
```

> `embed_texts(list[str]) -> list[vector]` + `model_id`/`dim` 만 고정하면
> store/search/insights는 무변경, 모델 교체는 config + 재인덱싱(§9)으로 끝난다.

## 트레이드오프 / 주의
- **모델 번들 용량**: 인프로세스 모델은 ~100~500MB. 배포 패키지에 포함하거나 최초 실행 시 다운로드.
- **첫 로드 지연**: 프로세스 시작 시 모델 적재(수 초). MCP는 장수 프로세스라 1회 비용.
- **모델 교체 = 전체 재임베딩**: 다른 모델 벡터는 호환 불가 (index.html §06 주의와 동일).
- **CPU 성능**: ONNX 양자화 모델이면 개인 규모 코퍼스에서 CPU로 충분. 대량이면 GPU 옵션 고려.

## 결론
Ollama는 **임베딩 호출을 인프로세스 라이브러리(권장: fastembed/ONNX)로 바꾸면 완전히 제거 가능**하다.
생성 LLM은 Claude가 담당하므로 로컬엔 인코더만 있으면 되고, 그래서 데몬리스 구성이 자연스럽다.
