DOCKER_TAG=latest

# Determine which OS.
OS?=$(shell uname -s | tr A-Z a-z)

default: build

clean:
	-rm -rf dist

test-clean:
	rm -rf .tox/

build: clean
	pip install --upgrade pip setuptools wheel pbr twine
	python setup.py sdist bdist_wheel
	pip install dist/Opsy*.whl

run-tests:
	tox

test: test-clean
	tox

test-verbose:
	tox -v

docker-build: build
	docker build -t objectrocket/opsy:latest .

docker-deploy: docker-build
	docker tag objectrocket/opsy:latest objectrocket/opsy:$(DOCKER_TAG)
	docker push objectrocket/opsy:$(DOCKER_TAG)
	docker push objectrocket/opsy:latest
