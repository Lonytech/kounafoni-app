#!/bin/bash

# Before server launch
echo "🔵 Flask only server launching..."

# export necessary env var
export FLASK_ENV=production

# Start flask landing page
poetry run gunicorn -b 0.0.0.0:5000 src.app.app:app
