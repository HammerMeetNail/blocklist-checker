FROM python:3.6.9-alpine as Deploy

WORKDIR /app
COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY gunicorn.py .
COPY web /app/web

ENTRYPOINT [ "gunicorn", "-c", "gunicorn.py", "wsgi:app" ]