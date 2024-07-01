FROM ollama/ollama

ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/root/.local/bin:$PATH"

ENV HOST 0.0.0.0

# Update package list and install pipx
RUN apt-get update -y && \
    apt-get install -y ffmpeg && \
#    apt-get install -y nginx && \
#    addgroup --system nginx && \
#    adduser --system --ingroup nginx nginx && \
    apt-get install -y pipx && \
    pipx install poetry==1.7.1 && \
    rm -rf /var/lib/apt/lists/*

# Copy Nginx config
#COPY nginx/nginx.conf /etc/nginx/nginx.conf
#COPY nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf

# Set the working directory
WORKDIR /kounafoni_app

# Copy the current directory contents into the container
COPY . .

# Install dependencies with poetry
RUN poetry install --no-root --no-cache --without explo && \
    chmod +x pull_ollama_models_and_launch_app_servers.sh

EXPOSE 8080 8000

ENTRYPOINT ["./pull_ollama_models_and_launch_app_servers.sh"]

#CMD ["/bin/sh", "poetry", "run", "chainlit", "run", "--watch", "--headless", "src/chatbot.py", "&", "poetry", "run", "gunicorn", "-b", "0.0.0.0:8080", "src.app.app:app", "&"]

#CMD poetry run chainlit run --watch --headless src/chatbot.py & poetry run gunicorn -b 0.0.0.0:8080 src.app.app:app &
