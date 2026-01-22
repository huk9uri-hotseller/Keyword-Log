DB_URL=postgresql://klog:klog@localhost:5432/klog
PSQL=docker exec -i klog-postgres psql -U klog -d klog


.PHONY: db-up db-down db-reset db-logs db-psql db-schema

db-up:
	docker compose up -d
	@echo "Waiting for Postgres to be ready..."
	@until docker exec klog-postgres pg_isready -U klog -d klog > /dev/null 2>&1; do sleep 1; done
	@echo "Postgres is ready."

db-down:
	docker compose down

db-reset:
	docker compose down -v
	docker compose up -d
	@echo "Waiting for Postgres to be ready..."
	@until docker exec klog-postgres pg_isready -U klog -d klog > /dev/null 2>&1; do sleep 1; done
	@echo "Postgres is ready."

db-logs:
	docker logs -f klog-postgres

db-psql:
	$(PSQL)

db-schema:
	$(PSQL) -f db/schema.sql
