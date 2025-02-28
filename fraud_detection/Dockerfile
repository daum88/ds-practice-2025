FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r fraud_detection/requirements.txt
CMD ["python", "fraud_detection/src/app.py"]
