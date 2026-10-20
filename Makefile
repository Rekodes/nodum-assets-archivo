.DEFAULT_GOAL := help
SHELL := /bin/bash

REGISTRY ?= docker.io/rekodes
VERSION ?= 0.2.0
PLATFORM ?= linux/amd64
# Cada temática es una carpeta con sus datasets y sus algoritmos; generic/ vale para cualquiera.
THEMES := $(patsubst %/datasets/,%,$(wildcard */datasets/))
ALGORITHMS := $(basename $(wildcard */algorithms/*.py))
image = $(REGISTRY)/nodum-$(subst _,-,$(notdir $(1))):$(VERSION)

help: ## Esta ayuda
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-8s %s\n", $$1, $$2}'

data: ## Regenera los datasets y comprueba que no cambian
	@for t in $(THEMES); do \
	  for g in $$t/datasets/generadores/*.py; do python3 -I "$$g" $$t/datasets || exit 1; done; \
	  (cd $$t/datasets && shasum -a 256 -c SHA256SUMS --quiet) || exit 1; \
	  test "$$(find $$t/datasets/sinteticos -type f | wc -l)" -eq "$$(wc -l < $$t/datasets/SHA256SUMS)" \
	    || { echo "$$t: hay ficheros que no están en SHA256SUMS" >&2; exit 1; }; \
	  echo "$$t: datasets sin cambios"; done

lint: ## Ruff y mypy estricto sobre los algoritmos
	uvx ruff check --line-length 120 --select E,F,I,B,UP,SIM,N shared */algorithms */datasets/generadores scripts
	MYPYPATH=shared uvx mypy --strict --python-version 3.12 shared/*.py */algorithms/*.py scripts/*.py

build: ## Construye las imágenes (linux/amd64)
	@for a in $(ALGORITHMS); do n=$$(basename $$a); \
	  docker buildx build --platform $(PLATFORM) -f shared/Dockerfile --build-arg ALGORITHM=$$a \
	    -t $(REGISTRY)/nodum-$${n//_/-}:$(VERSION) --load . || exit 1; done

# Como el nodo: sin red, 1000:1000, sin capacidades y las entradas de solo lectura.
run: ## Ejecuta una imagen: make run a=line_count in="agro/datasets/…" [params='{…}']
	@test -n "$(a)" -a -n "$(in)" || { echo 'uso: make run a=line_count in="agro/datasets/…"' >&2; exit 1; }
	@work=$$(mktemp -d); mkdir -p $$work/inputs $$work/outputs; chmod 777 $$work/outputs; \
	  cp $(in) $$work/inputs/; echo '$(or $(params),{})' > $$work/inputs/algoCustomData.json; \
	  docker run --rm --platform $(PLATFORM) --network none --user 1000:1000 --cap-drop ALL \
	    -v $$work/inputs:/data/inputs:ro -v $$work/outputs:/data/outputs $(call image,$(a)) \
	  && echo "salidas en $$work/outputs" && ls $$work/outputs

push: ## Sube a tu Docker Hub un algoritmo, una carpeta o todos: make push a=water_stress_model|agro|all [ns=…]
	@python3 scripts/push_images.py $(a) --version $(VERSION) $(if $(ns),--namespace $(ns)) $(if $(force),--force)

.PHONY: help data lint build run push
