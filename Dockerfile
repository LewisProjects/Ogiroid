FROM python:3.11-alpine
LABEL org.opencontainers.image.authors="Jason Cameron <jason@jasoncameron.dev>, Levani Vashadze <vashadzelevani11@gmail.com>"
LABEL org.opencontainers.image.source="https://github.com/LewisProjects/Ogiroid"
ENV PYTHONDONTWRITEBYTECODE 1 
ENV PYTHONUNBUFFERED 1
COPY requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt  --no-cache-dir
COPY . .
CMD ["python3", "-O", "main.py"]
