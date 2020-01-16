FROM python:3.6 as builder

ENV REPO_PATH=/opsy
COPY . $REPO_PATH
COPY dist/Opsy*.whl $REPO_PATH
WORKDIR $REPO_PATH
RUN pip install dist/Opsy*.whl