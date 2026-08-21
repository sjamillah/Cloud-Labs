# Installing the dependencies(builder: stage 1)
FROM python:3.12-slim@sha256:2c941e860699f878900b0edc2403613c234d4b32eda3cc9fa7036991a2a63c4a AS builder
 
WORKDIR /app
 
COPY app/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
 
# Building the image(stage 2)
FROM python:3.12-slim@sha256:2c941e860699f878900b0edc2403613c234d4b32eda3cc9fa7036991a2a63c4a AS target
 
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
