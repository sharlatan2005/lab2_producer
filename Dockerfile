FROM python:3.12-slim AS base

FROM base AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --use-feature=fast-deps --prefer-binary -r requirements.txt


FROM base AS runner

COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

WORKDIR /app
COPY . .

EXPOSE 5000

ENTRYPOINT ["python", "app.py"]
