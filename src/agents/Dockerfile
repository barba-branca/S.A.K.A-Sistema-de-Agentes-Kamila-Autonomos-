# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Argument for the agent name
ARG AGENT_NAME

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's source code
COPY ./src /app/src

# Set the python path
ENV PYTHONPATH=/app

# Run the specified agent
CMD ["python", "-m", "src.agents.${AGENT_NAME}.main"]
