# localbrain — web/MCP 서버용 이미지 (옵션, 2차 배포 형태)
# GPU: 호스트에 NVIDIA 드라이버 + Container Toolkit 필요. `docker run --gpus all ...`
#   (Windows 는 Docker Desktop + WSL2 백엔드에서 --gpus all 지원)
# 주의: 컨테이너는 마운트된 볼륨만 본다 → "임의 로컬 폴더 인덱싱" 대신
#   호스트 문서 폴더를 /docs 등으로 마운트해 서비스로 운용하는 시나리오에 적합.
FROM python:3.11-slim

WORKDIR /app

# torch (CUDA 12.6). CPU 전용으로 쓰려면 아래 줄을 제거하고 일반 torch 사용.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cu126

COPY . .
RUN pip install --no-cache-dir ".[st]"

# 데이터/모델 캐시는 볼륨으로 영속화
ENV LOCALBRAIN_HOME=/data/localbrain \
    HF_HOME=/data/hf \
    LOCALBRAIN_HOST=0.0.0.0 \
    LOCALBRAIN_PORT=8765
VOLUME ["/data", "/docs"]
EXPOSE 8765

CMD ["localbrain-web"]
