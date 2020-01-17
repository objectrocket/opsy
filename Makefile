DOCKER_TAG=latest

# Determine which OS.
OS?=$(shell uname -s | tr A-Z a-z)

default: build

clean:
	-rm -rf dist/*

clean-tests:
	rm -rf .tox/

build: clean
	pip install --upgrade -r build-requirements.txt
	python setup.py sdist bdist_wheel

install: build
	pip install dist/Opsy*.whl

run-tests:
	tox

test:
	tox

test-verbose:
	tox -v

docker-build: build
	docker build -t objectrocket/opsy:latest .

docker-deploy: docker-build
	docker tag objectrocket/opsy:latest objectrocket/opsy:$(DOCKER_TAG)
	docker push objectrocket/opsy:$(DOCKER_TAG)
	docker push objectrocket/opsy:latest
