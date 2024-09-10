# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8
ENV SHELL=/bin/bash LANG=en_US.UTF-8

RUN apt-get update && \
    apt-get install -y gettext locales && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /app

# Copy the current directory contents into the container at /app
COPY . /app/

# Set the working directory in the container
WORKDIR /app

# Install dependencies
RUN pip install --upgrade pip && pip install -q -r requirements.txt