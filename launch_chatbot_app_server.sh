#!/bin/bash
set -m

# Start Ollama in the background.
ollama serve & poetry run chainlit run --headless src/chatbot.py &
#P1=$!
# Start Ollama in the background.
#apt update -y && apt install -y systemd
#systemctl start ollama

# Pause for Ollama to start.
sleep 5

echo "🔵 Retrieving models..."
#echo mayflowergmbh/occiglot-7b-fr-en-instruct orca-mini | xargs -n1 ollama pull
ollama pull mayflowergmbh/occiglot-7b-fr-en-instruct
ollama pull sammcj/sfr-embedding-mistral:Q4_K_M
echo "🟢 Done!"
#sleep 5

# export necessary env var
#echo "Exporting CHATBOT_ENV var"
#export CHATBOT_ENV=production
#export CHATBOT_ENV=debug

# restart ollama
#systemctl start ollama
# Pause before server launch
#echo "🔵 Launching chainlit chatbot app..."

# Start Chainlit
#poetry run chainlit run --headless src/chatbot.py &
#P2=$!
#
#wait $P1 $P2

# now we bring the primary process back into the foreground
# and leave it there
ollama serve &

wait
