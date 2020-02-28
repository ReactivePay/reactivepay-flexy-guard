FROM python:3.7.2-alpine3.9

ENV PYTHONUNBUFFERED 1

ENV APP_NAME /flexy-guard
RUN mkdir /$APP_NAME
WORKDIR /$APP_NAME

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /$APP_NAME