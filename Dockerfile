# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt /app/

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Expose the port that the app runs on
EXPOSE 8000

# Run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
