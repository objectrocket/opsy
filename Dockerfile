FROM python:3.6 as builder

ENV REPO_PATH=/opsy
COPY . $REPO_PATH
WORKDIR $REPO_PATH
RUN make build