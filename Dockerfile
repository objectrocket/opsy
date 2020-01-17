FROM python:3.6
LABEL maintainer="sre@objectrocket.com"

ENV PYTHONUNBUFFERED 1
ENV OPSY_CONFIG "/etc/opsy/opsy.toml"

COPY dist/Opsy*.whl /tmp

RUN set -ex; \
    mkdir /etc/opsy && \
    useradd -rmd /opt/opsy opsy && \
    python -m venv /opt/opsy && \
    /opt/opsy/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/opsy/bin/pip install --no-cache-dir /tmp/Opsy*.whl && \
    chown -R opsy: /opt/opsy /etc/opsy && \
    rm -rf /tmp/Opsy*.whl

COPY --chown=opsy:opsy scripts/entrypoint.sh /opt/opsy/bin/

USER opsy

EXPOSE 5000
ENTRYPOINT ["/opt/opsy/bin/entrypoint.sh"]
