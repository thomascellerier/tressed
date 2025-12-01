.PHONY: all
all: test

.PHONY: ruff-check
ruff-check:
	uv run ruff check

.PHONY: check-fmt
check-fmt:
	uv run ruff format --diff

.PHONY: fmt
fmt:
	uv run ruff check --select I --fix
	uv run ruff format

.PHONY: pytest
pytest:
	uv run pytest -vv

.PHONY: ty
ty-check:
	uv run ty check

.PHONY: mypy
mypy:
	uv run mypy --enable-incomplete-feature=TypeForm

.PHONY: lint
lint: mypy ruff-check check-fmt

.PHONY: test
test: lint pytest
