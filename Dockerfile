FROM python:3.9-slim
WORKDIR /app
COPY . /app
RUN pip install Flask gunicorn
RUN pip install google-cloud-datastore google-cloud-storage google-cloud-firestore google-cloud-secret-manager
RUN pip install firebase-admin
RUN pip install pyrebase4
EXPOSE 8080
CMD ["python", "project.py"]
