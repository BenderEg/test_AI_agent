up-local:
	docker compose -f docker-compose.yml up -d --build

pull-model:
	docker exec ollama ollama pull qwen2.5-coder:1.5b

down-local:
	docker compose -f docker-compose.yml down

lint:
	ruff check src/

format:
	ruff format src/

typecheck:
	mypy src/

test:
	pytest

check: lint typecheck test

install-hooks:
	cp hooks/pre-commit .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit