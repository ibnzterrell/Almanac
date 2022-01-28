FROM python:3.8-slim-buster

EXPOSE 80

WORKDIR /app

COPY api /app/api
COPY model /app/model
COPY services /app/services

COPY appAPI.py /app/appAPI.py
COPY .env /app/.env
COPY requirements.txt /app/requirements.txt

RUN python -m pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm

CMD ["python", "appAPI.py"]