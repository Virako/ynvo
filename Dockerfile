FROM python:3.13-alpine

WORKDIR /app

RUN pip install uv
COPY pyproject.toml uv.lock /app/
RUN uv sync --no-dev
COPY docker/entrypoint /usr/local/bin/entrypoint
RUN chmod +x /usr/local/bin/entrypoint
COPY . /app

CMD python3 manage.py collectstatic --noinput
