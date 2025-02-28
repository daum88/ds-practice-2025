# orchestrator/Dockerfile
FROM python:3.11
WORKDIR /app
# Copy the entire repository so shared files are available
COPY . .
RUN pip install --no-cache-dir -r orchestrator/requirements.txt
CMD ["python", "orchestrator/src/app.py"]
