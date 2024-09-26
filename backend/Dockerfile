FROM python:3.11-slim

# Install PostgreSQL client and other dependencies
RUN apt-get update && apt-get install -y postgresql postgresql-contrib libpq-dev gcc

# Set environment variables to prevent Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create and set the working directory
WORKDIR /app

# Copy the requirements.txt file
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of your Django project files
COPY . /app/

# Expose the port Django runs on
EXPOSE 8000

# Command to run the Django development server
CMD ["sh", "-c", "python manage.py runserver 0.0.0.0:8000"]
