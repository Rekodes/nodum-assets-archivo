.DEFAULT_GOAL := help
SHELL := /bin/bash

REGISTRY ?= docker.io/rekodes
VERSION ?= 0.1.0
PLATFORM ?= linux/amd64
ALGORITHMS := line-count data-quality dp-histogram hypoxia-model env-audit

help: ## Muestra esta ayuda
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

data: ## Regenera los datasets y comprueba que salen los mismos bytes (SHA256SUMS)
	@for g in datasets/generadores/*.py; do python3 -I "$$g" datasets || exit 1; done
	@cd datasets && shasum -a 256 -c SHA256SUMS --quiet && echo "datasets idénticos a los publicados"

test: data ## Los tests de los cinco algoritmos con los datasets
	python3 -m unittest discover -s tests -v

build: ## Construye las cinco imágenes (linux/amd64, la de los nodos)
	@for a in $(ALGORITHMS); do \
	  docker buildx build --platform $(PLATFORM) --build-arg ALGORITHM=$$a \
	    -t $(REGISTRY)/nodum-$$a:$(VERSION) --load algorithms || exit 1; done

# Como el nodo: sin red, 1000:1000, sin capacidades, las entradas de solo lectura.
# Uso: make run a=dp-histogram in="datasets/sinteticos/boyas-hipoxia/v1/site-a.json" params='{"epsilon":0.5}'
run: ## Ejecuta una imagen como el nodo: make run a=<algoritmo> in="<ficheros>" [params='{…}']
	@test -n "$(a)" -a -n "$(in)" || { echo 'uso: make run a=line-count in="datasets/…/fichero"' >&2; exit 1; }
	@work=$$(mktemp -d); mkdir -p $$work/inputs $$work/outputs; chmod 777 $$work/outputs; \
	  cp $(in) $$work/inputs/; echo '$(or $(params),{})' > $$work/inputs/algoCustomData.json; \
	  docker run --rm --platform $(PLATFORM) --network none --user 1000:1000 --cap-drop ALL \
	    -v $$work/inputs:/data/inputs:ro -v $$work/outputs:/data/outputs \
	    $(REGISTRY)/nodum-$(a):$(VERSION) && ls -l $$work/outputs && echo "salidas en $$work/outputs"

push: ## Sube las cinco imágenes a Docker Hub y escribe sus digests en algorithms/DIGESTS
	@: > algorithms/DIGESTS
	@for a in $(ALGORITHMS); do \
	  docker push -q $(REGISTRY)/nodum-$$a:$(VERSION) >/dev/null || exit 1; \
	  d=$$(docker buildx imagetools inspect $(REGISTRY)/nodum-$$a:$(VERSION) --format '{{json .Manifest.Digest}}' | tr -d '"'); \
	  echo "$(REGISTRY)/nodum-$$a:$(VERSION) $$d" | tee -a algorithms/DIGESTS; done

.PHONY: help data test build run push
