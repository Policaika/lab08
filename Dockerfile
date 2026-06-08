FROM python:3.10-alpine

WORKDIR /service

RUN apk add --no-cache gcc musl-dev

COPY app/requirements.txt .
RUN pip install --no-cache-dir \
    --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    --default-timeout=100 \
    -r requirements.txt

COPY app/ .

EXPOSE 8080

ENTRYPOINT ["python", "app.py"]
