FROM python:3.6 as builder

ARG github_user
ARG github_access_token

RUN git config \
  --global \
  url."https://${github_user}:${github_access_token}@github.com".insteadOf \
  "https://github.com"

ENV REPO_PATH=/opsy
COPY . $REPO_PATH
WORKDIR $REPO_PATH
RUN make build