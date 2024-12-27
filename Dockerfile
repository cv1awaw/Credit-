# Use an official lightweight Python image
FROM python:3.11-slim

# Create a working directory
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your bot code into the container
COPY . .

# Set the environment variable for the bot token
# (You can also pass this at runtime via `-e BOT_TOKEN=...`.)
ENV BOT_TOKEN=YOUR_BOT_TOKEN_HERE

# Allow output to appear immediately in Docker logs
ENV PYTHONUNBUFFERED=1

# Run the code
CMD ["python", "your_script_name.py"]
