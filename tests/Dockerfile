FROM circleci/python:3.7.2

USER root
WORKDIR /tests

COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY run_tests.sh /tests/
COPY docker/* /tests/

ENTRYPOINT [ "/bin/bash", "-c", "/tests/run_tests.sh" ]