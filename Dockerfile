FROM python:3.10-slim

# Install all required packages at once
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    npm \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy app
COPY . /app/
WORKDIR /app/

# Install python packages
RUN pip install -r requirements.txt

# Start command (FIXED)
CMD ["python3", "-m", "Elevenyts", "start"]
