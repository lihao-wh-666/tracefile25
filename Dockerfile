ARG PYTHON_VERSION=3.12-slim
FROM python:${PYTHON_VERSION} AS builder

LABEL maintainer="platform-jumper" \
      description="Platform Jumper Game - Multi-stage Docker image" \
      version="1.0.0"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev \
        libsdl2-dev \
        libsdl2-image-dev \
        libsdl2-mixer-dev \
        libsdl2-ttf-dev \
        libfreetype6-dev \
        libportmidi-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


FROM python:${PYTHON_VERSION} AS runtime-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libsdl2-2.0-0 \
        libsdl2-image-2.0-0 \
        libsdl2-mixer-2.0-0 \
        libsdl2-ttf-2.0-0 \
        libfreetype6 \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

RUN groupadd -r appuser \
    && useradd -r -g appuser -d /app -s /sbin/nologin appuser \
    && chown -R appuser:appuser /app


FROM runtime-base AS development

ENV APP_ENV=development \
    HEADLESS=true \
    SCREEN_WIDTH=960 \
    SCREEN_HEIGHT=640 \
    FPS=60

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        xvfb \
        x11vnc \
        fluxbox \
        xterm \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER appuser
COPY --chown=appuser:appuser . .

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD HEALTHCHECK=true python platform_jumper.py || exit 1

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "platform_jumper.py"]


FROM runtime-base AS production

ENV APP_ENV=production \
    HEADLESS=true \
    SCREEN_WIDTH=960 \
    SCREEN_HEIGHT=640 \
    FPS=60 \
    PYTHONOPTIMIZE=2

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        xvfb \
        x11vnc \
        fluxbox \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get clean

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
    && mkdir -p /data \
    && chown -R appuser:appuser /data

USER appuser
COPY --chown=appuser:appuser . .

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD HEALTHCHECK=true python platform_jumper.py || exit 1

VOLUME ["/data"]

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "platform_jumper.py"]


FROM runtime-base AS testing

ENV APP_ENV=testing \
    HEADLESS=true \
    HEALTHCHECK=true \
    HEALTHCHECK_MAX_FRAMES=300 \
    SCREEN_WIDTH=960 \
    SCREEN_HEIGHT=640 \
    FPS=60

USER appuser
COPY --chown=appuser:appuser . .

CMD ["python", "platform_jumper.py"]
