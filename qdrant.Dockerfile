FROM qdrant/qdrant:latest

# Install curl for health checks
RUN apt-get update -yq && apt-get install -yqq curl
