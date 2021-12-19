FROM python:3.9
RUN pip install pyphi
WORKDIR /iit-thesis
COPY *.py *.txt .
ENV PYPHI_WELCOME_OFF=yes
ENTRYPOINT ["python", "-u", "run.py"]
