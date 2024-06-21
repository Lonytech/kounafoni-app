FROM ollama/ollama

ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/root/.local/bin:$PATH"

# Update package list and install pipx
RUN apt-get update -y && \
    apt-get install -y ffmpeg && \
    apt-get install -y pipx && \
    pipx install poetry==1.7.1 && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /kounafoni_app

# Copy the current directory contents into the container
COPY . .

# Install dependencies with poetry
RUN poetry install --no-root --no-cache --without explo && \
    chmod +x pull_ollama_models_and_launch_app_servers.sh

EXPOSE 5000 8000

ENTRYPOINT ["./pull_ollama_models_and_launch_app_servers.sh"]
