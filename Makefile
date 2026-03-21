.PHONY: help dev up down build migrate seed test lint clean

help:           ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev:            ## Start all services for development
	docker-compose up --build

up:             ## Start services in background
	docker-compose up -d

down:           ## Stop all services
	docker-compose down

build:          ## Build all Docker images
	docker-compose build

migrate:        ## Run database migrations
	cd backend && flask db upgrade

seed:           ## Seed database with sample data
	cd backend && python scripts/seed_db.py

seed-kb:        ## Seed medical knowledge base
	cd backend && python scripts/seed_knowledge_base.py

test-backend:   ## Run backend tests
	cd backend && pytest

test-frontend:  ## Run frontend tests
	cd frontend && npm test

test:           ## Run all tests
	$(MAKE) test-backend
	$(MAKE) test-frontend

lint-backend:   ## Lint backend code
	cd backend && ruff check . && black --check .

lint-frontend:  ## Lint frontend code
	cd frontend && npm run lint && npm run type-check

lint:           ## Lint all code
	$(MAKE) lint-backend
	$(MAKE) lint-frontend

clean:          ## Remove all Docker volumes and containers
	docker-compose down -v --remove-orphans

logs:           ## Tail logs for all services
	docker-compose logs -f

shell-backend:  ## Open a shell in backend container
	docker-compose exec backend bash

shell-db:       ## Open psql shell
	docker-compose exec postgres psql -U medassist -d medassist
