FROM python:3.9
RUN pip install pyphi
WORKDIR /iit-thesis
COPY *.py *.txt pyphi_config.yml .
ENTRYPOINT ["python", "-u", "pqr-micro-phi.py"]
