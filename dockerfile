FROM python:3.8-slim

# Set environment variables
ENV FLASK_APP=search.py
ENV FLASK_RUN_HOST=0.0.0.0

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY . /app

# Specify the command to run on container start
CMD ["flask", "run"]
