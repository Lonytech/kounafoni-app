#!/bin/bash

# Start Ollama in the background.
ollama serve

# Pause for Ollama to start.
sleep 5

echo "🔵 Retrieving models..."
ollama pull mayflowergmbh/occiglot-7b-fr-en-instruct
ollama pull sammcj/sfr-embedding-mistral:Q4_K_M
echo "🟢 Done!"

# Pause before server launch
echo "🔵 Launching chainlit chatbot app..."
sleep 5

# Start Chainlit
poetry run chainlit run --headless src/chatbot.py
