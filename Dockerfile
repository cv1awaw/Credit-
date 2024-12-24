# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot script
COPY main.py .

# Define environment variables (replace with your actual values or set them in Railway)
ENV BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN

# Run the bot
CMD ["python", "main.py"]
