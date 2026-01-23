.PHONY: install lint test unit integration up down

install:
	python -m pip install -r requirements.txt

test:
	python -m pytest -q

unit:
	python -m pytest -q tests/unit

integration:
	python -m pytest -q tests/integration

lint:
	ruff check .
	black --check .

up:
	docker compose up

down:
	docker compose down
