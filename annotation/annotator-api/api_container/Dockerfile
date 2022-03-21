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
# RUN python -m spacy download en_core_web_md
# RUN python -m spacy download en_core_web_lg
# RUN python -m spacy download en_core_web_trf
RUN python -m nltk.downloader wordnet
RUN python -m nltk.downloader omw-1.4
RUN pip install model/en_experimental_eddittree_ud_en_ewt-0.0.1.tar.gz

# Gunicorn bind / options are in gunicorn.conf.py
CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker"]