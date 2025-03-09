
FROM python:3.10

ENV PYTHONUNBUFFERED True


WORKDIR /app


COPY . /app


RUN pip install --no-cache-dir -r requirements.txt


ENV PORT 8080

CMD ["python", "main.py"]
