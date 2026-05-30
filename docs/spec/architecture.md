# localbrain — 아키텍처 & 작업량 산정

## 1. 아키텍처 한 장

```
[경로 입력]──┐
   파일/폴더  │  ① 수집·청킹·임베딩 (증분)
             ▼
        [벡터 DB: 문서 컬렉션]  ◀──검색──┐
                                        │
[Claude]──MCP──▶ search/add/list/reindex ┘
   │  질의 + 결과
   ▼
[질의 로그 + 질의 임베딩 컬렉션]  ──클러스터링──▶ [FAQ·인기주제·지식공백 리포트]
```

벡터 DB에 **두 컬렉션**을 둔다: 문서용(docs) / 질의용(queries).

## 2. 레이어 — 코어 라이브러리 + 얇은 어댑터

> 설계 원칙: **핵심 로직을 라이브러리로** 만들고, MCP·CLI·UI는 그 위의 얇은 어댑터로.
> → 나중에 UI를 붙여도 비용이 작아진다 ([`ui-review.md`](ui-review.md) 참조).

```
core/                      # 순수 라이브러리 (UI·MCP 무관)
  ingest.py    수집·청킹·증분
  embed.py     임베딩 (런타임 교체 가능 — embedding-runtime.md)
  store.py     벡터 DB (Chroma) 래퍼: docs / queries 컬렉션
  search.py    검색 (벡터 / 하이브리드)
  insights.py  질의 로깅 + 클러스터링 + 지식공백
adapters/
  mcp_server.py  # MCP 도구 (FastMCP)
  cli.py         # add/reindex/insights 등
  web/           # (선택) 인사이트 대시보드
```

## 3. 데이터 모델

**docs 컬렉션 (청크)** — 모델별로 버전 분리 (`docs__{model_id}`)
- `id`, `embedding`, **`text`(청크 원문 영속 보관)**
- metadata: `source_path`, `chunk_index`, `file_type`, `mtime`, `hash`, `indexed_at`
- > 청크 원문을 저장해두면 **모델 교체 시 재파싱 없이 임베딩만 다시** 만들면 된다(§9).

**queries 컬렉션 (질의)** — 역시 모델별 버전 분리
- `id`, `embedding`, `text(질의 원문 영속 보관)`
- metadata: `ts`, `top_score`, `result_ids`, `hit(검색 결과 유무)`, `feedback(선택)`, `cluster_id`

**collection_meta (활성 모델 추적)**
- `collection`, `model_id`, `dim`, `built_at`, `status(building|ready)`

**file_index (증분용, SQLite)**
- `path`, `hash`, `mtime`, `chunk_ids` → 변경/삭제 감지

## 4. MCP 도구 스펙

| 도구 | 입력 | 동작 |
|------|------|------|
| `search` | `query`, `k?`, `types?`, `path_filter?` | 의미(또는 하이브리드) 검색 → 청크+출처 반환. **질의 로깅·임베딩 동시 수행** |
| `add_path` | `path`, `recursive?`, `globs?` | 폴더/파일 인덱싱(증분) |
| `remove_path` | `path` | 소스 제거 + 해당 청크 삭제 |
| `list_sources` | — | 인덱싱된 소스·청크 수·최근 갱신 |
| `reindex` | `path?` | 변경분 재색인(없으면 전체 점검) |
| `query_insights` | `top_n?`, `since?` | 클러스터(FAQ)·인기주제·**지식공백(무응답 질의)** 리포트 |
| `switch_model` | `model_id` | 임베딩 모델 교체 → 새 컬렉션 재구축 후 원자적 전환 (§9) |
| `stats` | — | 인덱스 규모·활성 임베딩 모델·헬스 |

> 생성 LLM은 **Claude(클라이언트)**가 담당하므로 도구는 "검색·관리"에 집중. 로컬 생성 LLM 불필요.

## 5. 파이프라인

**수집(ingest)**: 경로 walk → 포맷별 로더 → 청킹(Recursive, 300~800토큰+overlap) → 임베딩 → store.
증분: `hash/mtime` 비교로 변경 파일만, 삭제 파일은 청크 제거 (상세 §10).

**검색(search)**: 질의 임베딩 → docs 컬렉션 top-k (옵션: BM25와 RRF 융합) → 출처 포함 반환.
동시에 질의 임베딩을 queries 컬렉션에 적재(축 C).

**인사이트(insights)**: queries 임베딩에 **HDBSCAN** 군집화 → 군집별 대표질의·빈도(FAQ),
`hit=false`/`top_score<θ` 질의 = **지식공백**. (군집 라벨은 필요 시 Claude가 명명 — 로컬 LLM 불필요)

## 6. 단계별 계획 & 산정 (1인, Python, 인프로세스 임베딩, 개인 규모)

| 단계 | 컴포넌트 | 작업량 |
|------|---------|--------|
| A | 경로 인덱싱 (md/txt + pdf/docx/코드, 청킹, Chroma, **증분**) | 2~3일 |
| B | MCP 서버 (위 도구 + stdio) | 1일 |
| C | 질의 임베딩·로깅 (검색 임베딩 재사용) | 0.5~1일 |
| D | 클러스터링 인사이트 (HDBSCAN·대표질의·지식공백·리포트) | 2일 |
| E | 설정·CLI·패키징 (stdio 오염 방지·에러·로깅·Windows) | 1~2일 |
| F | 테스트·튜닝 (청크/k/한국어/하이브리드) | 1~2일 |
| opt | 하이브리드(BM25+벡터 RRF) +0.5~1일 · 리랭킹 +0.5일 · 자동 인덱싱(스케줄/watcher §10.3) +0.5~1일 | — |

- **MVP**: ~1주 · **견고·범용**: ~2~3주 · **OSS 기반+C·D 신규**: ~1주(권장)

## 7. 스택
- **Python 권장**: 로더·청킹·임베딩·**클러스터링(HDBSCAN/scikit-learn/UMAP)** 생태계 성숙.
- 임베딩: 인프로세스(ONNX) — [`embedding-runtime.md`](embedding-runtime.md).
- 벡터 DB: ChromaDB(개인 규모) → 대규모 시 Qdrant.
- MCP: `mcp` Python SDK (FastMCP), stdio.
- **.NET 대안**: Atlas 스택 일관성은 좋으나 클러스터링·로더를 직접 구현 → A·D 1.5~2배. 범용 도구엔 비추천.

## 8. 리스크 (산정을 흔드는 변수)
1. **파일 포맷 범위** — 최대 scope creep. PDF(표/스캔 OCR)·Office·HWP로 가면 급증. MVP는 md/txt.
2. **증분 정확성** — 수정/삭제/이동, 대용량, 부분 재색인.
3. **클러스터링 실효성** — 콜드스타트(질의 누적 전 무의미), 라벨링, 갱신 주기. 가치 불확실성 최대.
4. **한국어** — 임베딩 모델(`bge-m3`)·청킹. 모델 교체 시 전체 재임베딩.
5. **규모** — 개인용 Chroma 충분, 대규모면 Qdrant + 작업.
6. **패키징** — MCP stdio 순수성, Windows 배포, (Ollama 제거 시) 모델 번들.

## 9. 모델 교체(swappability) 설계 — 1급 요구사항

> 목표: 임베딩 모델을 **나중에 쉽게 교체**하되, **재인덱싱 비용은 감수**한다.

서로 다른 모델은 **차원·벡터공간이 호환되지 않으므로** 섞을 수 없다. 따라서:

1. **Provider 추상화** — 임베딩을 `EmbeddingProvider` 인터페이스 뒤로 숨긴다
   (`embed_texts`, `model_id`, `dim`). 구현체: fastembed/sentence-transformers/ollama/onnx/cloud.
   교체는 **config 한 줄** ([`embedding-runtime.md`](embedding-runtime.md) 참조).
2. **컬렉션 버전 분리** — `docs__{model_id}` 처럼 모델별 컬렉션을 따로 둔다. `collection_meta`로 활성 모델 추적.
3. **원자적 전환(zero-downtime)** — `switch_model` 시:
   ```
   기존 컬렉션(ready) 유지 → 새 모델로 새 컬렉션 build(status=building)
   → 완료되면 active 포인터 전환(ready) → 옛 컬렉션 drop
   ```
   재구축 중에도 검색은 기존 모델로 계속 동작.
4. **원문 보관으로 재임베딩 저비용** — 청크/질의 **텍스트를 저장**해두므로, 교체는
   **파일 재파싱·재청킹 없이 저장된 텍스트만 다시 임베딩**하면 된다. (질의 컬렉션도 동일하게 재임베딩)
5. **진행 표시** — 재구축은 길 수 있으므로 진행률/ETA를 UI·`stats`로 노출 ([`ui-review.md`](ui-review.md)).

> 핵심: "텍스트 영속 보관 + 모델별 컬렉션 + 원자적 전환" 세 가지면 모델 교체가 안전·반복 가능해진다.

## 10. 증분 인덱싱 & 인덱싱 트리거

### 10.1 소스는 "경로"로 등록·구분
- `source = {path(폴더/파일), globs, recursive, source_id}`. **폴더 소스는 하위 신규 파일을 자동 편입**.
- 청크 metadata에 `source_path` 보관 → "특정 폴더만 검색"(`search`의 `path_filter`) 가능.
- 겹치는 소스(폴더 A와 그 하위 A/b 동시 등록 등)는 **정규화된 절대경로로 dedup** → 한 파일 중복 색인 방지.
- 단일 파일도 자체 소스로 등록 가능.

### 10.2 변경 감지 (`file_index` 기준)
소스 트리를 glob 적용해 walk 하고, `file_index`(path·hash·mtime·size·chunk_ids)와 대조한다.

- **2단계 시그니처**(성능): ① `mtime+size`로 빠르게 사전 필터 → ② 달라진 파일만 `content hash`(예: xxhash/SHA-256)로 확정.
- 분기:

| 상태 | 판정 | 처리 |
|------|------|------|
| **신규** | 경로가 `file_index`에 없음 | 청킹·임베딩·추가, 기록 생성 |
| **수정** | hash 변경 | 옛 청크 삭제(`chunk_ids`) → 재청킹·재임베딩, 기록 갱신 |
| **불변** | hash 동일 | **스킵** (증분의 핵심) |
| **삭제** | 기록엔 있으나 디스크에 없음 | 청크·기록 제거 |
| **이동/리네임** | 삭제+신규로 관측 | 기본은 그대로 처리. (옵션) hash 매칭 시 경로만 갱신, 재임베딩 생략 |

- 삭제 판정은 **소스의 경로+glob 범위로 한정**("소스 X 아래 현재 발견된 파일" vs "소스 X로 기록된 파일") → 범위 밖 청크 오삭제 방지.
- 재임베딩 입도: **MVP는 파일 단위**(파일이 바뀌면 그 파일 청크 전체 재생성). 최적화로 청크 단위 diff 가능.
- 모델 교체로 인한 전체 재구축은 §9 — 여기 증분과 별개 경로.

### 10.3 인덱싱 트리거 — 수동 외 방법
> **증분 엔진은 하나**(10.2), 트리거만 여러 개를 조합한다.

| 트리거 | 동작 | 장단점 |
|--------|------|--------|
| **수동** | 버튼 / CLI / MCP `reindex` | 명확한 제어 (기준) |
| **시작 시 reconcile** | 서비스 기동 시 1회 증분 스캔 | 꺼진 동안의 변경분 보정 → **항상 켜둘 것** (watcher 공백도 메움) |
| **스케줄(주기)** | N분/시간마다 증분 | 단순·비용 한정, 지연은 주기만큼 |
| **실시간 watcher** | `watchdog`로 등록 폴더 감시 → 변경 파일만 즉시 증분 | 항상 최신. 단 이벤트 폭주(디바운스 필요)·임시파일 필터·OS watch 한계·앱 미실행 구간 |
| **검색 시(opt-in)** | `search`에 `ensure_fresh` 옵션 → 사전 신선도 점검 후 검색 | 검색 지연 추가 |

- **권고**: 시작 reconcile + 스케줄(기본) + 실시간 watcher(토글) + 수동 override.
- **MVP**: 수동 + 시작 reconcile. 이후 스케줄·watcher 추가.
- watcher 구현 시: 디바운스(예 2s)로 저장 1회의 연속 이벤트를 1패스로 합치고, `.tmp / ~$* / .swp / .git/` 등 무시.
- 진행상황은 `ui-review.md` Indexing 탭/SSE로 노출.
