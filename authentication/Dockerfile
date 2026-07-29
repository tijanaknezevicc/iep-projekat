FROM python:3

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY main.py /main.py
COPY models.py /models.py
COPY configuration.py /configuration.py

ENTRYPOINT ["python", "main.py"]