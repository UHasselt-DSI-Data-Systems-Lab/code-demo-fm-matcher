FROM python:3.12-slim

COPY . /app
WORKDIR /app

run pip install -r requirements.txt

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "--server.port", "8501", "--server.address", "0.0.0.0", "--server.enableCORS", "false", "--server.enableXsrfProtection", "false", "main.py"]
