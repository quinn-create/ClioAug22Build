FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MCP_TRANSPORT=http \
    HOST=0.0.0.0 \
    PORT=8080

WORKDIR /app

RUN addgroup --system --gid 10001 mcp \
    && adduser --system --uid 10001 --gid 10001 --home /app --disabled-password mcp

COPY pyproject.toml README.md ./
COPY clio_aug22_build ./clio_aug22_build

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir . \
    && chown -R mcp:mcp /app

USER mcp

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT','8080'))"

CMD ["python", "-m", "clio_aug22_build"]
