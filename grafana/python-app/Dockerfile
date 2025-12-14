FROM python:3.9

WORKDIR /app
COPY app.py /app
RUN pip install flask prometheus_client

CMD ["python", "app.py"]
