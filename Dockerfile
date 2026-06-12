# Stage 1: build React frontend
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Python runtime
FROM python:3.12-slim
WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY --from=frontend /app/frontend/dist ./dist

EXPOSE 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
