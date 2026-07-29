COMPOSE ?= docker compose

.DEFAULT_GOAL := help
.PHONY: help build up down restart status logs bootstrap test monitoring console caputlog clean

help: ## Show available targets
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

build: ## Build all container images
	$(COMPOSE) --profile test --profile tools build

up: ## Start the core stack (IOCs, gateways, archiver, alarms, exporter)
	$(COMPOSE) up -d

down: ## Stop the stack (data volumes are kept)
	$(COMPOSE) down

restart: ## Restart the core stack
	$(COMPOSE) restart

status: ## Show service status and health
	$(COMPOSE) ps

logs: ## Tail logs (use S=<service> to filter, e.g. make logs S=ioc-cryo)
	$(COMPOSE) logs -f $(S)

bootstrap: ## Submit PVs to the archiver and import the alarm configuration
	$(COMPOSE) --profile tools run --rm archiver-bootstrap
	$(COMPOSE) --profile tools run --rm alarm-import

test: ## Run the containerized integration test suite
	$(COMPOSE) --profile test run --rm tests

monitoring: ## Start the Prometheus + Grafana monitoring profile
	$(COMPOSE) --profile monitoring up -d

console: ## Attach to an IOC shell via procServ (use I=<service>, default ioc-cryo)
	$(COMPOSE) exec $(or $(I),ioc-cryo) console

caputlog: ## Follow the central log of CA puts (who changed which PV)
	$(COMPOSE) exec caputlog tail -f /logs/caput.log

clean: ## Stop everything and remove volumes (DESTROYS archived data)
	$(COMPOSE) --profile monitoring --profile test --profile tools down -v
