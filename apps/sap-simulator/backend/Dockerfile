FROM python:3.12-slim

WORKDIR /app

# Copy dependencies
COPY .venv /app/.venv_temp

# Alternatively, copy requirements and install
RUN pip install --no-cache-dir fastapi uvicorn pydantic faker pandas openpyxl

# Copy project files
COPY apps/sap-simulator/backend /app/apps/sap-simulator/backend
COPY apps/shared /app/apps/shared

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["python", "apps/sap-simulator/backend/main.py"]
