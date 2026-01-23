.PHONY: install lint test unit integration up down

install:
	python -m pip install -r requirements.txt

lint:
	ruff check .
	black --check .

unit:
	python -m pytest tests/unit -q

integration:
	python -m pytest tests/integration -q

test: unit integration

up:
	docker compose up

down:
	docker compose down
