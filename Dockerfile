# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create a non-root user
RUN useradd --create-home appuser
USER appuser

# Copy the requirements file into the container
COPY --chown=appuser:appuser requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy the rest of the application code into the container
COPY --chown=appuser:appuser . .

# Ensure the PATH includes the user's local bin
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Expose the port the app runs on
EXPOSE 8000

# Default command to run the app (can be overridden in docker-compose)
# This is useful for running the container directly
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "main:app"]
