# ---- build stage: install deps into a venv, keeps final image lean ----
FROM python:3.12-slim AS build

WORKDIR /build
COPY app/requirements.txt .
RUN python -m venv /venv \
    && /venv/bin/pip install --no-cache-dir --upgrade pip \
    && /venv/bin/pip install --no-cache-dir -r requirements.txt

# ---- final stage: copy only the venv + app code, run as non-root ----
FROM python:3.12-slim

RUN addgroup --system app && adduser --system --ingroup app app
WORKDIR /app

COPY --from=build /venv /venv
COPY app/app.py .

ENV PATH="/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PORT=5000

USER app
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
