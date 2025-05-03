# Use an official Python runtime as the base image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Start with hot-reload (you already mount utils/ and src/ as volumes)
CMD ["python", "utils/other/hotreload.py", "payment/src/app.py"]
