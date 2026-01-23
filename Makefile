install:
	python -m pip install -r requirements.txt

test:
	python -m pytest -q

lint:
	ruff check .
	black --check .

up:
	docker compose up

down:
	docker compose down
