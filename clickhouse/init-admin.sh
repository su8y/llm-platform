#!/bin/bash
# This script runs after ClickHouse initialization to set the correct password

if [ -f /var/lib/clickhouse/uuid ]; then
    # Database already initialized, update the password hash
    if [ -n "$CLICKHOUSE_USER" ] && [ -n "$CLICKHOUSE_PASSWORD" ]; then
        PASSWORD_HASH=$(echo -n "$CLICKHOUSE_PASSWORD" | sha256sum | cut -d' ' -f1)

        cat > /etc/clickhouse-server/users.d/default-user.xml << EOF
<clickhouse>
  <users>
    <default remove="remove" />

    <$CLICKHOUSE_USER>
      <profile>default</profile>
      <networks>
        <ip>::/0</ip>
      </networks>
      <password_sha256_hex>$PASSWORD_HASH</password_sha256_hex>
      <quota>default</quota>
      <access_management>${CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT:-0}</access_management>
    </$CLICKHOUSE_USER>
  </users>
</clickhouse>
EOF
        echo "Updated password hash for user $CLICKHOUSE_USER"
    fi
fi