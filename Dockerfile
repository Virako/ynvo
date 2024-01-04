FROM python:3.11-alpine

WORKDIR /app

RUN apk add pango gcc musl-dev py3-wheel python3-dev libffi-dev zlib-dev jpeg-dev
COPY requirements.txt /app
RUN pip install -U pip
RUN pip install -r requirements.txt
COPY docker/entrypoint /usr/local/bin/entrypoint
RUN chmod +x /usr/local/bin/entrypoint
COPY . /app

CMD python3 manage.py collectstatic --noinput
