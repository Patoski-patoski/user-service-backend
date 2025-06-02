FROM python:3.10-slim

WORKDIR /app
COPY requirements/base.txt requirements/prod.txt ./requirements/
RUN pip install --no-cache-dir -r requirements/prod.txt

COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]