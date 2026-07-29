FROM python:3

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY configuration.py /configuration.py
COPY connections.py /connections.py
COPY decorators.py /decorators.py
COPY director.py /director.py

ENTRYPOINT ["python", "director.py"]