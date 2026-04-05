# Use a lightweight Python image
FROM python:3.12-slim

# Install uv (Fastest way to manage dependencies)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory inside the container
WORKDIR /app

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1

# Copy the dependency files first (for faster builds)
COPY pyproject.toml uv.lock ./

# Install dependencies (frozen ensures it matches your local setup exactly)
RUN uv sync --frozen --no-install-project --no-dev

# Copy the rest of your application code
COPY . .

# Expose the port your FastAPI app runs on
EXPOSE 8000

# Set environment variables to ensure Python output is visible in logs
ENV PYTHONUNBUFFERED=1

# The command to start your server
# We use 0.0.0.0 so it's accessible from outside the container
CMD ["uv", "run", "python", "-m", "server.app"]
