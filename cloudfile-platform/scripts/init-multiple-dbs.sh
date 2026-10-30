#!/bin/bash
# Creates multiple databases in the Postgres container at startup.
# Reads POSTGRES_MULTIPLE_DATABASES (comma-separated) from the environment.
set -euo pipefail

function create_database() {
	local db="$1"
	echo "Creating database '$db'"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
		SELECT 'CREATE DATABASE $db'
		WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$db')\gexec
	EOSQL
}

if [ -n "${POSTGRES_MULTIPLE_DATABASES:-}" ]; then
	echo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"
	IFS=',' read -ra DBS <<<"$POSTGRES_MULTIPLE_DATABASES"
	for db in "${DBS[@]}"; do
		create_database "$(echo "$db" | xargs)"
	done
	echo "Multiple databases created"
fi
