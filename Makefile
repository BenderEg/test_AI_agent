up-local:
	docker compose -f docker-compose.yml up -d --build

pull-model:
	docker exec ollama ollama pull llama3

down-local:
	docker compose -f docker-compose.yml down

lint:
	ruff check src/

format:
	ruff format src/

typecheck:
	mypy src/

check: lint typecheck

install-hooks:
	cp hooks/pre-commit .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit