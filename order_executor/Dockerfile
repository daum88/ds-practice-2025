# order_executor/Dockerfile

FROM python:3.11-slim
WORKDIR /app

# Install required dependencies
RUN pip install grpcio grpcio-tools protobuf

# Copy application source code
COPY src/ /app/

# Copy gRPC generated protobuf files into container (from local pb_generated folder)
COPY pb_generated/*.py /app/

# Set the entrypoint command
CMD ["python", "executor_service.py"]
