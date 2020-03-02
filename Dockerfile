# --- Build Stage ----
FROM python:3.6.9-alpine as Build

WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY gunicorn.py wsgi.py ./
COPY web /app/web

ENTRYPOINT [ "gunicorn", "-c", "gunicorn.py", "wsgi:app" ]

# --- Test Stage ----
FROM Build as Test

WORKDIR /app
COPY test /app/test
RUN pip install -r test/requirements.txt

ENV AWS_ACCESS_KEY_ID mock
ENV AWS_SECRET_ACCESS_KEY mock
ENV AWS_DEFAULT_REGION mock

RUN pytest test/unit.py --doctest-modules -v --cov web --cov-report term-missing

# --- Release Stage ---
FROM Build as Release
