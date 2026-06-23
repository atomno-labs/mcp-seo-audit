# Multi-stage build for the Glama MCP analyzer (docker build + docker run -i).
# Stdio MCP server — entrypoint is the console script `atomno-mcp-seo-audit`.
FROM python:3.12-slim AS build
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src/ src/
RUN pip install --no-cache-dir .

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd --create-home --shell /bin/bash mcp
WORKDIR /home/mcp
COPY --from=build /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=build /usr/local/bin/atomno-mcp-seo-audit /usr/local/bin/atomno-mcp-seo-audit
USER mcp
ENTRYPOINT ["atomno-mcp-seo-audit"]
