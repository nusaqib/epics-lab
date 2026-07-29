FROM python:3.12-slim

COPY requirements.txt /tests/requirements.txt
RUN pip install --no-cache-dir -r /tests/requirements.txt

COPY . /tests
WORKDIR /tests

ENTRYPOINT ["pytest", "-v", "--color=yes"]
