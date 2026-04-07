# Use a lightweight Python image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Set environment variables to ensure Python output is visible in logs
# and to avoid creating .pyc files in the container
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy the requirements file first (for faster builds using Docker cache)
COPY requirements.txt .

# Install dependencies using standard pip
# --no-cache-dir keeps the image size small
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Expose the port your FastAPI app runs on
EXPOSE 8000

# The command to start your server
# We use python -m to ensure the server package is found correctly
CMD ["python", "-m", "server.app"]
