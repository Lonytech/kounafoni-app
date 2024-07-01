#!/bin/bash

# Start Ollama in the background.
ollama serve &

# Pause for Ollama to start.
sleep 5

#echo "🔵 Retrieving models..."
#ollama pull mayflowergmbh/occiglot-7b-fr-en-instruct
#ollama pull sammcj/sfr-embedding-mistral:Q4_K_M
#echo "🟢 Done!"

# Pause before server launch
echo "🔵 Launching Servers (Flask and Chainlit) ..."
sleep 5

# Start Flask in production mode
#export FLASK_APP=src/app/app.py
#export FLASK_ENV=production

# Start Chainlit
poetry run chainlit run --headless src/chatbot.py &

# start flask landing page
poetry run gunicorn -b 0.0.0.0:8080 src.app.app:app &

# Start Nginx
#nginx -g "daemon off;"

# Wait for both background processes to exit
wait
