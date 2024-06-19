############ Using python as parent layer ##############
FROM python:3.10.12-slim-bullseye

ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory
WORKDIR /kounafoni_app

# Copy the current directory contents into the container
COPY . .

RUN apt update -y && \
    apt install curl -y && \
    curl -sSL https://install.python-poetry.org | python3 - --version 1.8.1 && \
    export PATH="$HOME/.local/bin:$PATH" && \
    poetry self add poetry-plugin-export && \
    poetry export -f requirements.txt --without-hashes --output requirements.txt # && \
#    pip install --no-cache-dir -r requirements.txt && \
#    curl -fsSL https://ollama.com/install.sh | sh
#
## make sh executable
#RUN chmod +x pull_ollama_models.sh && \
#    chmod +x launch_app_servers.sh
#
#ENTRYPOINT ["./pull_ollama_models.sh"]
#
#CMD ["./launch_app_servers.sh"]

############ Using ollama as parent layer ##############
#FROM ollama/ollama
#
#ENV DEBIAN_FRONTEND=noninteractive \
#    PATH="/root/.local/bin:$PATH" \
#    POETRY_ARTIFACTS_CACHE_DIR=/tmp/poetry_cache/artifacts
#
## Update package list and install pipx
#RUN apt-get update -y && \
#    apt-get install -y pipx && \
#    pipx install poetry==1.7.1
#
## Set the working directory
#WORKDIR /kounafoni_app
#
## Copy the current directory contents into the container
#COPY . .
#
## Install dependencies with poetry
#RUN poetry install && rm -rf $POETRY_CACHE_DIR
#
## make sh executable
#RUN chmod +x pull_ollama_models.sh

#ENTRYPOINT ["./pull_ollama_models.sh"]

#CMD ["poetry", "run", "python", "src/app/app.py"]





#
## Stage 1: Build
#FROM ollama/ollama AS builder
#
#ENV DEBIAN_FRONTEND=noninteractive
#ENV PATH="/root/.local/bin:$PATH"
#
## Update package list and install pipx
#RUN apt-get update -y && \
#    apt-get install -y pipx && \
#    pipx ensurepath && \
#    pipx install poetry==1.7.1
#
## Set the working directory
#WORKDIR /kounafoni_app
#
## Copy the current directory contents into the container
#COPY . .
#
## Install dependencies with poetry
#RUN poetry install --without explo
#
## Stage 2: Runtime
#FROM ollama/ollama
#
#ENV PATH="/root/.local/bin:$PATH"
#
## Copy only the necessary parts from the builder stage
#COPY --from=builder /root/.local /root/.local
#COPY --from=builder /kounafoni_app /kounafoni_app
#
## Set the working directory
#WORKDIR /kounafoni_app
#
## make sh executable
#RUN chmod +x pull_ollama_models.sh
#
##ENTRYPOINT ["./pull_ollama_models.sh"]
#
##CMD ["poetry", "run", "python", "src/app/app.py"]
