# Use an official Python runtime as a base image
FROM python:3.11-slim

# Install PostgreSQL client
RUN apt-get update && apt-get install -y postgresql postgresql-contrib libpq-dev gcc

# Set environment variables to prevent Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create and set the working directory
WORKDIR /app

# Install Django and other Python dependencies
RUN pip install --upgrade pip
RUN pip install django psycopg2-binary
RUN pip install django-cors-headers
RUN pip install djangorestframework
RUN pip install requests

# Expose the port Django runs on
EXPOSE 8000

# Command to run the Django development server
CMD ["sh", "-c", "django-admin startproject fantasy_trades_app . && python manage.py runserver 0.0.0.0:8000"]
