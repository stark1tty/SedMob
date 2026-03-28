FROM python:3.12-slim

WORKDIR /app

COPY sedmob/requirements.txt sedmob/requirements.txt
RUN pip install --no-cache-dir -r sedmob/requirements.txt gunicorn

COPY run.py .
COPY sedmob/ sedmob/

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
