.PHONY: up down migrate seed dump reset rollback clean

# Start the database container.
up:
	docker compose up -d --wait

# Stop the database container (data is preserved).
down:
	docker compose down

# Apply all pending up migrations.
migrate:
	@bash migrate.sh up

# Reset DB to seed state (rolls back if ahead, migrates forward if behind).
seed:
	@bash seed.sh

# Dump all table data into seeds/ — commit to share with the team.
dump:
	@bash dump.sh

# Wipe the volume and rebuild from scratch.
reset:
	docker compose down -v
	$(MAKE) up
	$(MAKE) seed

# Roll back migrations above N.  Usage: make rollback N=2
rollback:
	@bash migrate.sh down $(N)

# Truncate all data tables, leaving schema and migration history intact.
clean:
	@bash clean.sh
