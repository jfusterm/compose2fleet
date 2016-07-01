.PHONY: docker build install clean

IMAGE = compose2fleet
VERSION = 0.0.1

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

