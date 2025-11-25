FROM python:3.11

# Create a directory with proper permissions
RUN mkdir -p /app/files && chmod 777 /app/files

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]