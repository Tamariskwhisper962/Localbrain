# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); versioning is [SemVer](https://semver.org/).

## [Unreleased]

## [0.1.1] - 2026-05-30
### Added
- 웹 UI 로딩 스피너(검색·인사이트) + 실패 시 에러 표시
### Changed
- 임베딩 모델 **lazy 로드** — AppContext/MCP 핸드셰이크 즉시, `stats`/`list-sources`는 모델 로드 없이 동작
### Fixed
- CLI 출력 UTF-8 고정 — Windows cp949 콘솔에서 한국어/em-dash 출력 시 크래시 방지
- 릴리즈 워크플로: `skip-existing`(재실행 안전), publish 잡에 `contents: read`

## [0.1.0] - 2026-05-30
### Added
- 경로(폴더/파일) 기반 증분 인덱싱 (mtime+hash 변경 감지, 삭제/수정 처리)
- 의미 검색 + Cross-Encoder 리랭킹(`BAAI/bge-reranker-v2-m3`)
- 질의 임베딩 로깅 및 클러스터링 인사이트(FAQ·지식공백)
- 어댑터 3종: CLI(`localbrain`), MCP stdio 서버(`localbrain-mcp`), 운영 웹 콘솔(`localbrain-web`)
- 임베딩 provider 교체 구조: fastembed(ONNX, 기본) / sentence-transformers(bge-m3) / ollama
- 모델별 벡터 컬렉션 버전 분리 + 코사인 거리, 모델 교체용 `--rebuild`
- GPU(CUDA) 자동 사용, `fp16` 옵션

[Unreleased]: https://github.com/sinwoo0225/Localbrain/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/sinwoo0225/Localbrain/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/sinwoo0225/Localbrain/releases/tag/v0.1.0
