RELEASE_VERSION := $(shell git describe --exact-match --tags $$(git log -n1 --pretty='%h') 2> /dev/null)
PACKAGE_VERSION := $(shell python setup.py --version 2> /dev/null)
CHART_VERSION := $(shell egrep '^version:' helm/opsy/Chart.yaml | sed 's/^version: \(.*\)$$/\1/')+$(PACKAGE_VERSION)

# Utility targets
.PHONY: default versions clean clean-tests install

default: build

versions:
	# Just prints out the detected versions based on setuptools and git tags.
	@echo PACKAGE_VERSION=$(PACKAGE_VERSION)
	@echo RELEASE_VERSION=$(RELEASE_VERSION)
	@echo CHART_VERSION=$(CHART_VERSION)

clean:
	python setup.py clean
	rm -rf dist/*

clean-tests:
	rm -rf .tox/

install:
	pip install -e .


# Test targets
.PHONY: test-code test-style test-build test-release test

test-code:
	tox -e code

test-style:
	tox -e style
	helm lint helm/opsy/

test-build:
	# Make sure our files are named correctly
	test -s dist/python/Opsy-$(PACKAGE_VERSION)-py3-none-any.whl
	test -s dist/python/Opsy-$(PACKAGE_VERSION).tar.gz
	# Run twine checks
	twine check dist/python/Opsy-$(PACKAGE_VERSION)-py3-none-any.whl dist/python/Opsy-$(PACKAGE_VERSION).tar.gz
	# Check helm build
	helm lint dist/helm/opsy-$(CHART_VERSION).tgz

test-release:
	# Make sure package version matches git tag.
	test "$(RELEASE_VERSION)" = "$(PACKAGE_VERSION)"
	# Make sure our files are named correctly
	test -s dist/python/Opsy-$(RELEASE_VERSION)-py3-none-any.whl
	test -s dist/python/Opsy-$(RELEASE_VERSION).tar.gz
	# Run twine checks
	twine check dist/python/Opsy-$(RELEASE_VERSION)-py3-none-any.whl dist/python/Opsy-$(RELEASE_VERSION).tar.gz

test: test-code test-style


# Build targets
.PHONY: build-requirements build-python build-docker build-helm build
build-requirements:
	pip install --upgrade -r build-requirements.txt

build-python:
	mkdir -p dist/python/
	python setup.py sdist -d dist/python bdist_wheel -d dist/python

build-docker:
	mkdir -p dist/docker/
	docker build -t objectrocket/opsy:$(PACKAGE_VERSION) --build-arg OPSY_VERSION=$(PACKAGE_VERSION) .
	docker save objectrocket/opsy:$(PACKAGE_VERSION) | gzip > dist/docker/Opsy-$(PACKAGE_VERSION).tar.gz

build-helm:
	mkdir -p dist/helm/
	helm package helm/opsy/ -d dist/helm/ --app-version $(PACKAGE_VERSION) --version $(CHART_VERSION)

build: build-requirements clean build-python build-docker build-helm test-build


# Release targets
.PHONY: release-dockerhub release-pypi release

release-dockerhub:
	@docker login -u $${DOCKER_USER} -p $${DOCKER_PASS}
	docker tag objectrocket/opsy:${RELEASE_VERSION} objectrocket/opsy:latest
	docker push objectrocket/opsy:$(RELEASE_VERSION)
	docker push objectrocket/opsy:latest

release-pypi:
	twine upload --non-interactive dist/python/Opsy-$(RELEASE_VERSION)-py3-none-any.whl dist/python/Opsy-$(RELEASE_VERSION).tar.gz

release: test-release release-pypi release-dockerhub

