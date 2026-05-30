# localbrain — 로드맵 / 남은 작업

> 갱신: 2026-05-30 · 현재: **PyPI `localbrain-rag` 0.1.1 배포됨** (0.1.0은 망가져 yank 필요)

체크박스로 진행 상황을 추적하세요. `[유저]` = PyPI/GitHub 웹에서 직접, `[코드]` = 소스 작업.

---

## ✅ 완료 (참고)
- [x] MVP: 경로 인덱싱(증분) · 의미검색 · 리랭킹(bge-reranker-v2-m3) · 질의 클러스터링 인사이트
- [x] 어댑터 3종: CLI · MCP(stdio) · 웹 콘솔
- [x] GPU(CUDA) 사용, 임베딩 lazy 로드(MCP 핸드셰이크 즉시), fp16 옵션
- [x] 패키징: pyproject 메타데이터 · package-data(웹 정적) · LICENSE
- [x] CI/Release(OIDC Trusted Publishing) + **설치/import 검증 게이트**
- [x] PyPI 배포: **0.1.1** (0.1.0의 `__init__.py` 누락 버그 발견·수정)
- [x] 웹 UI 로딩 스피너 · CLI UTF-8 출력 · README 배지 · `.gitattributes` · 레포 About(설명·토픽)

---

## 🔴 릴리즈 마무리 (작고 명확)
- [ ] **[유저] 0.1.0 yank** — PyPI → localbrain-rag → Manage → Releases → 0.1.0 → Yank (망가진 버전, 새 설치에서 숨김)
- [ ] **[유저] GitHub Release 노트(v0.1.1)** — `gh release create v0.1.1 --notes-from-tag` 또는 CHANGELOG 붙여넣기
- [ ] **[유저] LICENSE 저작권자** — "localbrain authors" → 실명/핸들로
- [ ] **[유저] MCP 등록(원할 때)** — `claude mcp add localbrain --scope user -- "<...>\.venv\Scripts\localbrain-mcp.exe"` 후 `/mcp` 확인
- [ ] (선택) 소셜 프리뷰 이미지 / 웹 콘솔 스크린샷을 README에

## 🟡 품질 · 안정성
- [ ] **[코드] 다중 프로세스 쓰기 일원화** — 겪었던 chroma stale 이슈 근본 해결.
      웹 백엔드가 인덱싱(쓰기) 소유, CLI/MCP는 웹 API 호출 또는 "웹 켜둔 채 CLI index 금지" 강제
- [ ] **[코드] `localbrain doctor`** — GPU/CUDA·torch 빌드·모델 캐시·활성 설정 점검 명령
- [ ] **[코드] 테스트 확대 + CI pytest** — 현재 클러스터링 단위테스트만.
      scanner(증분 감지)·indexer·search 테스트 추가, CI에 `pytest` 단계
- [ ] **[코드] 의존성 lock** — 재현성(현재 느슨한 `>=`). uv.lock 또는 constraints
- [ ] (선택) GitHub Actions 노드20 경고 — actions/checkout·setup-python 버전 상향

## 🔵 기능 확장
- [ ] **[코드] 하이브리드 검색**(BM25 + 벡터 RRF) — 정확 용어·약어·코드에 강해짐 (정확도 레버 1순위)
- [ ] **[코드] 자동 인덱싱 트리거** — watcher(watchdog) / 스케줄 / 시작 시 reconcile (현재 수동만)
- [ ] **[코드] PDF/Office 로더** — 현재 텍스트·마크다운만. `core/loaders/`에 추가 (PDF 표·스캔본 OCR은 별도 고려)
- [ ] **[코드] 모델 교체 시 진행 표시** — Model 탭 스피너 + 재구축 진행률(SSE)
- [ ] (선택) 클러스터 자동 라벨링 — 군집 이름을 Claude(MCP 클라이언트)에 맡겨 명명

---

## 추천 순서
1. **릴리즈 마무리**: 0.1.0 yank → v0.1.1 릴리즈 노트 (가장 먼저, 짧음)
2. **하이브리드 검색**(🔵) — 사용 체감(정확도)이 가장 큼
3. **다중 프로세스 쓰기 일원화**(🟡) — 실사용 안정성
4. 그다음 doctor · 자동 인덱싱 · PDF 로더 · 테스트/lock

## 참고 메모
- 배포명은 `localbrain-rag`(PyPI), 명령/import는 `localbrain`.
- 공개용 기본 임베딩은 `fastembed multilingual-e5-large`(torch 불필요). 한국어 최상 품질은 `[st]` + bge-m3 + CUDA torch.
- 모델 교체 시 `localbrain index --rebuild` (모델별 컬렉션 분리, 코사인 거리).
- 다음 배포: `pyproject` version↑ → `git tag vX.Y.Z && git push origin vX.Y.Z` (release.yml가 publish, skip-existing 안전).
- 설계 상세는 [`docs/spec/`](spec/README.md).
