FROM python:3.9.6

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY / /src/
WORKDIR /src

CMD ["python3", "app.py"]