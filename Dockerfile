FROM python:3.10-bullseye@sha256:4ce711926e79e68e0b42d0330c8c246ef81d31a744016626
LABEL org.opencontainers.image.authors="Jason Cameron <jason@jasoncameron.dev>"
LABEL org.opencontainers.image.source="https://github.com/LewisProjects/Ogiroid"
ENV PYTHONDONTWRITEBYTECODE 1 
ENV PYTHONUNBUFFERED 1
COPY requirements.txt /app/
WORKDIR /app
RUN pip install -r -no-cache-dir requirements.txt 
COPY . .
CMD ["python3", "main.py"]
