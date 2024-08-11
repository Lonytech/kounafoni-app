#!/usr/bin/env bash

# Change the value in case you are in dev environment
export CHATBOT_ENV=production

# Run chainlit app from root directory (HOME=/root is for Cloud Run)
HOME=/root poetry run chainlit run --headless src/chatbot.py
