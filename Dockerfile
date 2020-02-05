FROM python:3.6-slim
ARG OPSY_VERSION
LABEL maintainer="sre@objectrocket.com"
LABEL opsy_version=$OPSY_VERSION

ENV PYTHONUNBUFFERED 1
ENV OPSY_CONFIG "/opt/opsy/opsy.toml"

RUN useradd -rmd /opt/opsy opsy

USER opsy

COPY --chown=opsy:opsy dist/python/Opsy-${OPSY_VERSION}-py3-none-any.whl /opt/opsy

RUN set -ex; \
    python -m venv /opt/opsy && \
    /opt/opsy/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/opsy/bin/pip install --no-cache-dir /opt/opsy/Opsy-${OPSY_VERSION}-py3-none-any.whl && \
    rm /opt/opsy/Opsy-${OPSY_VERSION}-py3-none-any.whl

COPY --chown=opsy:opsy scripts/entrypoint.sh /opt/opsy/bin/

EXPOSE 5000
ENTRYPOINT ["/opt/opsy/bin/entrypoint.sh"]
