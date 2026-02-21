# Build image with participant details
# docker build -t blk-hacking-ind-kiran-as .

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add pytest for testing
RUN pip install pytest

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5477", "--reload"]