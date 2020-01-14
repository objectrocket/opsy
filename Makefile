DOCKER_TAG=latest

# Determine which OS.
OS?=$(shell uname -s | tr A-Z a-z)

default: build

clean:
	-rm -r ./bin/ > /dev/null 2>&1

test-clean:
	@docker kill backups-tidy-tester; docker rm -f backups-tidy-tester

build:
	pip install opsy

run-tests:
	tox

test:
	tox

test-verbose:
	@docker run -d -p 5000:5000 --name opsy python:3.6-alpine;
	tox -v
	docker kill opsy; docker rm opsy

ci-test:
	@tox

docker-build:
	@docker build -t objectrocket/opsy:latest .

docker-deploy:
	@docker tag objectrocket/opsy:latest objectrocket/backups-tidy:$(DOCKER_TAG)
	@docker push objectrocket/opsy:$(DOCKER_TAG)
	@docker push objectrocket/opsy:latest