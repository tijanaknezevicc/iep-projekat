FROM python:3

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN python -c "from solcx import install_solc; install_solc('0.8.18')"

COPY configuration.py /configuration.py
COPY connections.py /connections.py
COPY decorators.py /decorators.py
COPY director.py /director.py
COPY solidity /solidity

ENTRYPOINT ["python", "director.py"]