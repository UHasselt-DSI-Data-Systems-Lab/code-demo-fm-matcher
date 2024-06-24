FROM python:3.12-slim

COPY . /app
WORKDIR /app

# WIP
#RUN pip install poetry
#RUN poetry install
# autoconf build-base cmake
#RUN apk add --no-cache build-base cmake apache-arrow-dev && pip install -r requirements.txt && apk del build-base cmake
run pip install -r requirements.txt

EXPOSE 8501


CMD ["poetry", "run", "streamlit", "run", "--server.port", "8501", "--server.address", "0.0.0.0", "--server.enableCORS", "false", "--server.enableXsrfProtection", "false", "main.py"]
