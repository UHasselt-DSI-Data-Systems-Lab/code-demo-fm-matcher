#!/bin/sh

# write a secret app password if provided
mkdir -p .streamlit
if [ -n "$SECRET_APP_PASSWORD" ]; then
	echo "password = \"$SECRET_APP_PASSWORD\"\n" > .streamlit/secrets.toml
fi

# start the app
python -m streamlit run --server.port 8501 --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false main.py
