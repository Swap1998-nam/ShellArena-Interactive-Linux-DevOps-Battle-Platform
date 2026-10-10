FROM python:3.14-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN groupadd --gid 10001 arena && useradd --uid 10001 --gid arena --no-create-home arena \
    && mkdir -p /app/data && chown arena:arena /app/data
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY --chown=arena:arena backend /app/backend
COPY --chown=arena:arena frontend /app/frontend
COPY --chown=arena:arena gunicorn.conf.py /app/gunicorn.conf.py
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=3)" || exit 1
CMD ["gunicorn", "--config", "gunicorn.conf.py", "backend.wsgi:app"]
