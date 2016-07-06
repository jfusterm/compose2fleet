.PHONY: docker build install clean

IMAGE = jfusterm/compose2fleet
VERSION := $(shell sed -nr 's/^[^0-9]*(([0-9]+\.)*[0-9]+).*/\1/p' compose2fleet/version.py)

default: build

docker:
	@docker build -t $(IMAGE):$(VERSION) .
	@docker tag $(IMAGE):$(VERSION) $(IMAGE):latest

build: 
	@python3 setup.py sdist

install:
	@python3 setup.py install

clean:
	@rm -rf build *egg* dist

