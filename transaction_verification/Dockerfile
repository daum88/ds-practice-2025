FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r transaction_verification/requirements.txt
CMD ["python", "transaction_verification/src/app.py"]
