FROM python:3.12-slim-trixie

# copy UV to our container
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app/

COPY ./uv.lock ./uv.lock
COPY ./pyproject.toml ./pyproject.toml

RUN uv venv
RUN uv sync --locked --no-dev --no-install-project

ENV PATH="/app/.venv/bin:$PATH"

RUN useradd --create-home appuser

COPY . .

RUN chown -R appuser:appuser /app

USER appuser


WORKDIR /app/diving_timer/

CMD ["/app/.venv/bin/gunicorn", "diving_timer.wsgi:application","--bind", "0.0.0.0:8000"]
