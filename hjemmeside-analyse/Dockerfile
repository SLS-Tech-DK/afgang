FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8080
# GEMINI_API_KEY sættes som env-var ved deploy (fra Bitwarden) — ikke i imaget.
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 120 main:app
