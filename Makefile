# Atalhos da trilha local (Docker no PC). Nada aqui toca a UI.
DC := docker compose

.PHONY: build up down sh test lint fmt check

build:
	$(DC) build

up:
	$(DC) up -d

down:
	$(DC) down

sh:
	$(DC) exec backend bash

test:
	$(DC) exec backend pytest

lint:
	$(DC) exec backend ruff check picockpit tests
	$(DC) exec backend black --check picockpit tests

fmt:
	$(DC) exec backend ruff check --fix picockpit tests
	$(DC) exec backend black picockpit tests

check: lint test
