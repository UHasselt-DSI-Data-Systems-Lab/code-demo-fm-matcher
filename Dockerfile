FROM python:3.12-slim

COPY . /app
WORKDIR /app

run pip install -r requirements.txt

EXPOSE 8501

ENTRYPOINT ["./entrypoint.sh"]
