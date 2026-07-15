run:
	python -m app.main

lint:
	ruff check --fix-only
	ruff format
	ruff check
