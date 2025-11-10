FROM python:3.12-slim
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app

# For pip requirements:
# COPY requirements.txt .
# RUN pip install -r requirements.txt

# For pyproject.toml:
COPY pyproject.toml .
RUN pip install .

COPY . .

# CMD ["python", "./diving_timer/manage.py", "runserver", "0.0.0.0:8000"]
