# Build image with participant details
# docker build -t blk-hacking-ind-kiran-as .

FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 5477
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5477"]