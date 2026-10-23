FROM python:3.11-slim

WORKDIR /app

# Que los print() lleguen al log de Docker en tiempo real
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

# pip y setuptools de la imagen base suelen traer vulnerabilidades conocidas
RUN pip install --no-cache-dir --upgrade pip setuptools \
    && pip install --no-cache-dir -r requirements.txt

COPY ./app /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]