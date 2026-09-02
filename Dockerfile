FROM python:3.12-alpine

RUN apk add --no-cache curl

COPY app.py /app.py

EXPOSE 80

CMD ["python", "/app.py"]
