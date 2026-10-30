#!/bin/sh
# Creates multiple databases in the Postgres container at startup.
# Reads POSTGRES_MULTIPLE_DATABASES (comma-separated) from the environment.
#
# POSIX /bin/sh only (the postgres:15-alpine image has no bash). Do NOT use
# bash-only features (function, local, <<<, arrays). Keep LF line endings.
set -eu

create_database() {
	db="$1"
	echo "Creating database '$db'"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
		SELECT 'CREATE DATABASE $db'
		WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$db')\gexec
	EOSQL
}

if [ -n "${POSTGRES_MULTIPLE_DATABASES:-}" ]; then
	echo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"
	# Split on commas without bash arrays: swap IFS and iterate.
	old_ifs="$IFS"
	IFS=','
	for db in $POSTGRES_MULTIPLE_DATABASES; do
		# Trim surrounding whitespace.
		trimmed="$(printf '%s' "$db" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
		if [ -n "$trimmed" ]; then
			create_database "$trimmed"
		fi
	done
	IFS="$old_ifs"
	echo "Multiple databases created"
fi
