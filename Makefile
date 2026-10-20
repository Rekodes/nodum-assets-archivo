.DEFAULT_GOAL := help
SHELL := /bin/bash

REGISTRY ?= docker.io/rekodes
VERSION ?= 0.2.0
PLATFORM ?= linux/amd64
ALGORITHMS := line_count data_quality dp_histogram hypoxia_model env_audit
image = $(REGISTRY)/nodum-$(subst _,-,$(1)):$(VERSION)

help: ## Esta ayuda
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-8s %s\n", $$1, $$2}'

data: ## Regenera los datasets y comprueba que no cambian
	@for g in datasets/generadores/*.py; do python3 -I "$$g" datasets || exit 1; done
	@cd datasets && shasum -a 256 -c SHA256SUMS --quiet && echo "datasets sin cambios"

lint: ## Ruff y mypy estricto sobre los algoritmos
	uvx ruff check --line-length 120 --select E,F,I,B,UP,SIM,N algorithms datasets/generadores
	cd algorithms && uvx mypy --strict --python-version 3.12 *.py

build: ## Construye las imágenes (linux/amd64)
	@for a in $(ALGORITHMS); do \
	  docker buildx build --platform $(PLATFORM) --build-arg ALGORITHM=$$a \
	    -t $(REGISTRY)/nodum-$${a//_/-}:$(VERSION) --load algorithms || exit 1; done

# Como el nodo: sin red, 1000:1000, sin capacidades y las entradas de solo lectura.
run: ## Ejecuta una imagen: make run a=line_count in="datasets/…" [params='{…}']
	@test -n "$(a)" -a -n "$(in)" || { echo 'uso: make run a=line_count in="datasets/…"' >&2; exit 1; }
	@work=$$(mktemp -d); mkdir -p $$work/inputs $$work/outputs; chmod 777 $$work/outputs; \
	  cp $(in) $$work/inputs/; echo '$(or $(params),{})' > $$work/inputs/algoCustomData.json; \
	  docker run --rm --platform $(PLATFORM) --network none --user 1000:1000 --cap-drop ALL \
	    -v $$work/inputs:/data/inputs:ro -v $$work/outputs:/data/outputs $(call image,$(a)) \
	  && echo "salidas en $$work/outputs" && ls $$work/outputs

push: ## Sube las imágenes a Docker Hub y escribe sus digests
	@for a in $(ALGORITHMS); do \
	  i=$(REGISTRY)/nodum-$${a//_/-}:$(VERSION); docker push -q $$i >/dev/null || exit 1; \
	  echo "$$i $$(docker buildx imagetools inspect $$i --format '{{json .Manifest.Digest}}' | tr -d '"')"; done

.PHONY: help data lint build run push
