FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    libcairo2 \
    libjpeg-dev \
    libpango1.0-dev \
    libgif-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9000", "--reload"]
