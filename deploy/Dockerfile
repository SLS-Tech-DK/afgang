# Alternativ til Cloud Functions: kør som container på Cloud Run.
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8080
CMD exec functions-framework --target=handler --port=$PORT
