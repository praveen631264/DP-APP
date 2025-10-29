# Use the base image we will create, which contains all dependencies
FROM doc-processing-base:latest

# The working directory is already set to /app in the base image

# Copy the new application-specific requirements file
COPY app.requirements.txt .

# Install the application-specific dependencies
RUN pip install -r app.requirements.txt

# Copy the application code into the container at /app
# This is the only part that will be re-built on most code changes
COPY . .

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable
ENV FLASK_APP=main:create_app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8080

# Run the command to start the Gunicorn server
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:create_app()"]
