.PHONY: install install-dev lint test unit integration up down quality complexity duplication deadcode typecheck security

install:
	python -m pip install -r requirements.txt

install-dev:
	python -m pip install -r requirements-dev.txt

lint:
	ruff check .
	black --check .

complexity:
	radon cc src/ -s -j

duplication:
	pylint src/ --disable=all --enable=duplicate-code

deadcode:
	vulture src/ --min-confidence=80

typecheck:
	mypy src/ --json --ignore-missing-imports

security:
	bandit -r src/ -f json

quality:
	python scripts/quality/run_quality.py --layer all

unit:
	python -m pytest tests/unit -q

integration:
	python -m pytest tests/integration -q

test: unit integration

up:
	docker compose up

down:
	docker compose down
