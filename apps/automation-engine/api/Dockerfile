FROM python:3.12-slim

# Install system dependencies for Playwright
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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python packages
RUN pip install --no-cache-dir fastapi uvicorn pydantic pandas openpyxl faker playwright

# Install playwright browser binaries
RUN playwright install chromium

# Copy project files
COPY apps/automation-engine /app/apps/automation-engine
COPY apps/shared /app/apps/shared

ENV PYTHONPATH=/app

EXPOSE 8001

CMD ["python", "apps/automation-engine/api/main.py"]
