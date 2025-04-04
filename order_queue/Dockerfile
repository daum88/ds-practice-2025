FROM python:3.11-slim

WORKDIR /app

COPY ./order_queue/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./order_queue/src ./order_queue/src
COPY ./utils ./utils

CMD ["python", "-u", "/app/order_queue/src/app.py"]
