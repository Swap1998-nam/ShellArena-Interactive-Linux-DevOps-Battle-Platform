.PHONY: setup run test lint security up down
setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements-dev.txt
	.venv/bin/python scripts/bootstrap.py
run:
	.venv/bin/python scripts/serve.py
test:
	.venv/bin/pytest --cov=backend --cov-report=term-missing --cov-report=xml
lint:
	.venv/bin/ruff check backend tests scripts
	node --check frontend/app.js
security:
	.venv/bin/bandit -q -r backend -ll
	.venv/bin/pip-audit -r backend/requirements.txt
up:
	docker compose up --build -d
down:
	docker compose down
