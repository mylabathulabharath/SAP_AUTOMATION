FROM python:3.12-slim

# Install system dependencies for Playwright, X11, VNC, and noVNC
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    # GUI and VNC dependencies
    xvfb \
    x11vnc \
    fluxbox \
    novnc \
    websockify \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python packages
RUN pip install --no-cache-dir fastapi uvicorn pydantic pandas openpyxl faker playwright

# Install playwright browser binaries
RUN playwright install chromium

# Copy project files
COPY apps/automation-engine /app/apps/automation-engine
COPY apps/shared /app/apps/shared

# Copy startup script
COPY apps/automation-engine/api/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PYTHONPATH=/app
ENV DISPLAY=:99

EXPOSE 8001
EXPOSE 6080

ENTRYPOINT ["/entrypoint.sh"]
