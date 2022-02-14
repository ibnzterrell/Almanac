FROM python:3.10-bullseye

EXPOSE 80

WORKDIR /app

COPY api /app/api
COPY model /app/model
COPY services /app/services

COPY gunicorn.conf.py /app/gunicorn.conf.py
COPY main.py /app/main.py
COPY .env /app/.env
COPY requirements.txt /app/requirements.txt

RUN python -m pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm

# Gunicorn bind / options are in gunicorn.conf.py
CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker"]