FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r backend/requirements.txt
RUN pip install --no-cache-dir -r tests/requirements.txt

ENV PYTHONPATH="/app:${PYTHONPATH}"

CMD ["python", "-u", "tests/test_query.py"]
