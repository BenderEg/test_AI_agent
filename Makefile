up-local:
	docker compose -f docker-compose.yml up -d --build

pull-model:
	docker exec ollama ollama pull llama3

down-local:
	docker compose -f docker-compose.yml down