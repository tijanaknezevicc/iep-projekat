FROM python:3

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY configuration.py /configuration.py
COPY connections.py /connections.py
COPY decorators.py /decorators.py
COPY employee.py /employee.py

ENTRYPOINT ["python", "employee.py"]