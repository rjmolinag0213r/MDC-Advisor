# NextStop: one container serves the API and the built React app.
# Build:  docker build -t nextstop .
# Run:    docker run -p 5000:5000 --env-file backend/.env nextstop

FROM node:22-alpine AS web
WORKDIR /web
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY index.html index.tsx index.css App.tsx types.ts vite.config.ts tsconfig.json ./
COPY components ./components
COPY services ./services
RUN npm run build

FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 HOST=0.0.0.0 PORT=5000
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=web /web/dist /app/dist
RUN rm -f .env && useradd --create-home --uid 10001 app && mkdir -p data && chown -R app /app/backend/data
USER app
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:5000/api/health',timeout=4)"
CMD ["python", "app.py"]
