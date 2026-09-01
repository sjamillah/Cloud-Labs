# Installing the dependencies(builder: stage 1)
FROM python:3.12-slim@sha256:e5c9fa26ffb76e11e0f054f30dc2523a2f9693f0c36c0cf1e39b27e152d899fc AS builder
 
WORKDIR /app
 
COPY app/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
 
# Building the image(stage 2)
FROM python:3.12-slim@sha256:e5c9fa26ffb76e11e0f054f30dc2523a2f9693f0c36c0cf1e39b27e152d899fc AS target
 
# Provenance lives inside the image, not in the tag. Only :latest is pushed,
# so every superseded build is untagged - these labels are what still tie any
# image, found by digest, back to the exact commit that produced it.
ARG GIT_SHA=unknown
ARG BUILD_TIME=unknown
LABEL org.opencontainers.image.title="Neatly" \
      org.opencontainers.image.description="JSON formatter and validator" \
      org.opencontainers.image.source="https://github.com/sjamillah/Cloud-Labs" \
      org.opencontainers.image.revision="$GIT_SHA" \
      org.opencontainers.image.created="$BUILD_TIME"

# Creating a dedicated non-root user - the container never runs as root
RUN useradd --create-home --shell /bin/bash appuser
 
WORKDIR /app
 
# Bringing in only the installed packages from the builder stage - no compilers, no pip cache
COPY --from=builder /root/.local /home/appuser/.local
 
# Copying just the application code
COPY app/ .
 
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
 
RUN chown -R appuser:appuser /app /home/appuser/.local
 
USER appuser
 
EXPOSE 8080
 
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1
 
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "main:app"]
