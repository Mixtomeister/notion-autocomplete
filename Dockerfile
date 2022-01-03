FROM python:3.9.9

WORKDIR /app

COPY . /app/

RUN pip install -r requirements.txt