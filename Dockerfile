# Start from an official Python image. "slim" means it's a minimal install
# — smaller image size, faster to download and deploy.
FROM python:3.12-slim

# Set the working directory inside the container. All subsequent commands
# run from here, and your app files will live here.
WORKDIR /app

# Copy requirements first — before copying your code. This is intentional:
# Docker caches each step. If your code changes but requirements don't,
# Docker reuses the cached dependency install instead of re-running it.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the app.
COPY . .

# Tell Docker this container listens on port 8000.
EXPOSE 8000

# The command that runs when the container starts.
# Note: no --reload here — that's for development only.
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
