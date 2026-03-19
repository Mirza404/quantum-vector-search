.PHONY: db-up db-down db-migrate db-seed db-dump db-reset db-rollback

## Start the database container.
db-up:
	docker compose -f db/docker-compose.yml up -d --wait

## Stop the database container (data is preserved).
db-down:
	docker compose -f db/docker-compose.yml down

## Apply all pending up migrations.
db-migrate:
	@bash db/migrate.sh up

## Reset DB to seed state (rolls back if ahead, migrates forward if behind).
db-seed:
	@bash db/seed.sh

## Roll back migrations above N.  Usage: make db-rollback N=2
db-rollback:
	@bash db/migrate.sh down $(N)

## Dump all table data into db/seeds/ — commit to share with the team.
db-dump:
	@bash db/dump.sh

## Full reset: wipe the volume and rebuild from scratch.
db-reset: db-down
	docker compose -f db/docker-compose.yml down -v
	$(MAKE) db-up
	$(MAKE) db-seed
