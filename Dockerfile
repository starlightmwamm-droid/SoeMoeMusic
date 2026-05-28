FROM python:3.10-slim

# Install all required packages at once
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    npm \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# copy app
COPY . /app/
WORKDIR /app/

# install python packages
RUN pip install -r requirements.txt

# start command
CMD bash start
