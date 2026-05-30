# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); versioning is [SemVer](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-05-30
### Added
- 경로(폴더/파일) 기반 증분 인덱싱 (mtime+hash 변경 감지, 삭제/수정 처리)
- 의미 검색 + Cross-Encoder 리랭킹(`BAAI/bge-reranker-v2-m3`)
- 질의 임베딩 로깅 및 클러스터링 인사이트(FAQ·지식공백)
- 어댑터 3종: CLI(`localbrain`), MCP stdio 서버(`localbrain-mcp`), 운영 웹 콘솔(`localbrain-web`)
- 임베딩 provider 교체 구조: fastembed(ONNX, 기본) / sentence-transformers(bge-m3) / ollama
- 모델별 벡터 컬렉션 버전 분리 + 코사인 거리, 모델 교체용 `--rebuild`
- GPU(CUDA) 자동 사용, `fp16` 옵션

[Unreleased]: https://github.com/sinwoo0225/Localbrain/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/sinwoo0225/Localbrain/releases/tag/v0.1.0
