#!/bin/bash

# Start Ollama in the background.
ollama serve &

# Pause for Ollama to start.
sleep 5

echo "🔵 Retrieving models..."
ollama pull mayflowergmbh/occiglot-7b-fr-en-instruct
ollama pull sammcj/sfr-embedding-mistral:Q4_K_M
echo "🟢 Done!"

# Pause before server launch
echo "🔵 Launching Servers (Flask and Chainlit) ..."
sleep 5

# Start Flask in production mode
export FLASK_APP=src/app/app.py
export FLASK_ENV=production

# start flask landing page
poetry run python -m gunicorn -b 0.0.0.0:5000 src.app.app:app &

# Start Chainlit
poetry run python -m chainlit run --watch --headless src/chatbot.py &

# Wait for both background processes to exit
wait
