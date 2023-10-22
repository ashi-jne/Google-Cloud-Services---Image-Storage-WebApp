FROM python:3.9-slim

WORKDIR /app
COPY . /app
RUN pip install Flask gunicorn
RUN pip install google-cloud-datastore google-cloud-storage
EXPOSE 8080
CMD ["python", "project2.py"]

