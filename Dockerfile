FROM python:3.11

WORKDIR /front-init
VOLUME /front-init/storage

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p storage
RUN touch storage/data.json

CMD ["python", "main.py"]
