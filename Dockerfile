# Use an official lightweight Python image
FROM python:3.11-slim

# Create a working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your main.py bot code into the container
COPY main.py . 

# Set the environment variable for the bot token
# (You can override at runtime with -e BOT_TOKEN=...)
ENV BOT_TOKEN=YOUR_BOT_TOKEN_HERE

# Allow output to appear immediately in Docker logs
ENV PYTHONUNBUFFERED=1

# Run the code
CMD ["python", "main.py"]
