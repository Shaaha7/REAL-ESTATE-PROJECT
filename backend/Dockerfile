FROM python:3.11-slim
WORKDIR /app
ENV PYTHONPATH=/app
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
# torch is a transitive dep (via sentence-transformers, for the RAG embedder)
# and this app never uses a GPU. Installing it from the default index pulls
# the CUDA-bundled build - 3+ GB of nvidia_* wheels that go completely
# unused here and routinely time out mid-download. Installing the CPU-only
# build first satisfies later version constraints without pulling any of that.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p data/raw data/processed data/documents data/models data/evaluation logs mlruns
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 CMD curl -f http://localhost:${API_PORT:-8000}/api/health || exit 1
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${API_PORT:-8000}"]
