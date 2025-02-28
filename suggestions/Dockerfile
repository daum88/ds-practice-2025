FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r suggestions/requirements.txt
CMD ["python", "suggestions/src/app.py"]
