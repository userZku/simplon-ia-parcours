FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

WORKDIR /app

# Dépendances Python en premier pour optimiser le cache Docker.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code applicatif et modèle entraîné.
COPY app/ ./app/
COPY model/ ./model/

# Exécution non-root.
RUN useradd --create-home --shell /usr/sbin/nologin appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]