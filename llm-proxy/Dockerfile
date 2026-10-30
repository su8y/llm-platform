FROM python:3.14-slim

WORKDIR /home/app

COPY requirements.lock .
RUN pip3 install --no-cache-dir --require-hashes -r requirements.lock

COPY . .

EXPOSE 9999

CMD ["python3", "main.py"]
