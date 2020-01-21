RELEASE_VERSION := $(shell git describe --exact-match --tags $$(git log -n1 --pretty='%h') 2> /dev/null)
PACKAGE_VERSION := $(shell python setup.py --version 2> /dev/null)

default: build

versions:
	# Just prints out the detected versions based on setuptools and git tags.
	@echo PACKAGE_VERSION=$(PACKAGE_VERSION)
	@echo RELEASE_VERSION=$(RELEASE_VERSION)

clean:
	python setup.py clean
	rm -rf dist/*

clean-tests:
	rm -rf .tox/

build-requirements:
	pip install --upgrade -r build-requirements.txt

build-wheel:
	python setup.py sdist bdist_wheel

build-docker:
	docker build -t objectrocket/opsy:$(PACKAGE_VERSION) --build-arg OPSY_VERSION=$(PACKAGE_VERSION) .

build-test:
	# Make sure our files are named correctly
	test -s dist/Opsy-$(PACKAGE_VERSION)-py3-none-any.whl
	test -s dist/Opsy-$(PACKAGE_VERSION).tar.gz
	# Run twine checks
	twine check dist/Opsy-$(PACKAGE_VERSION)-py3-none-any.whl dist/Opsy-$(PACKAGE_VERSION).tar.gz

build: build-requirements clean build-wheel build-docker build-test

install:
	pip install -e .

test:
	tox

release-test:
	# Make sure package version matches git tag.
	test "$(RELEASE_VERSION)" = "$(PACKAGE_VERSION)"
	# Make sure our files are named correctly
	test -s dist/Opsy-$(RELEASE_VERSION)-py3-none-any.whl
	test -s dist/Opsy-$(RELEASE_VERSION).tar.gz
	# Run twine checks
	twine check dist/Opsy-$(RELEASE_VERSION)-py3-none-any.whl dist/Opsy-$(RELEASE_VERSION).tar.gz

release-dockerhub:
	@docker login -u $${DOCKER_USER} -p $${DOCKER_PASS}
	docker tag objectrocket/opsy:${RELEASE_VERSION} objectrocket/opsy:latest
	docker push objectrocket/opsy:$(RELEASE_VERSION)
	docker push objectrocket/opsy:latest

release-pypi:
	twine upload --non-interactive dist/Opsy-$(RELEASE_VERSION)-py3-none-any.whl dist/Opsy-$(RELEASE_VERSION).tar.gz

release: release-test release-pypi release-dockerhub

