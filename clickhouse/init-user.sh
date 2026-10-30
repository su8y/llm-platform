#!/bin/bash
set -e

# Wait for ClickHouse to be ready
until clickhouse-client --query "SELECT 1" > /dev/null 2>&1; do
    echo "Waiting for ClickHouse to be ready..."
    sleep 2
done

# Create admin user if doesn't exist
clickhouse-client --query "CREATE USER IF NOT EXISTS ${CLICKHOUSE_USER} IDENTIFIED WITH plaintext_password BY '${CLICKHOUSE_PASSWORD}' SETTINGS profile='default'" || true

# Grant all privileges
clickhouse-client --query "GRANT ALL ON *.* TO ${CLICKHOUSE_USER} WITH GRANT OPTION" || true

# Create database if specified
if [ -n "${CLICKHOUSE_DB}" ] && [ "${CLICKHOUSE_DB}" != "default" ]; then
    clickhouse-client --query "CREATE DATABASE IF NOT EXISTS ${CLICKHOUSE_DB}" || true
fi

echo "ClickHouse user initialization completed"