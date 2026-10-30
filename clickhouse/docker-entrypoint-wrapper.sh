#!/bin/bash
set -e

# Start the original entrypoint in background
/entrypoint.sh &
CLICKHOUSE_PID=$!

# Wait for ClickHouse to be ready
echo "Waiting for ClickHouse to start..."
for i in {1..60}; do
    if clickhouse-client --query "SELECT 1" > /dev/null 2>&1; then
        echo "ClickHouse is ready!"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "Timeout waiting for ClickHouse"
        exit 1
    fi
    sleep 1
done

# Fix password if using plaintext with special characters
if [ -n "$CLICKHOUSE_USER" ] && [ -n "$CLICKHOUSE_PASSWORD" ]; then
    echo "Checking password configuration for user $CLICKHOUSE_USER..."

    # Use double SHA256 as ClickHouse expects
    PASSWORD_HASH=$(echo -n "$CLICKHOUSE_PASSWORD" | sha256sum | awk '{print $1}' | xxd -r -p | sha256sum | awk '{print $1}')

    # Wait a bit more for config to be fully loaded
    sleep 3

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

    # Reload configuration multiple times to ensure it's applied
    for i in {1..3}; do
        clickhouse-client --query "SYSTEM RELOAD CONFIG" 2>/dev/null && break
        sleep 2
    done

    echo "Password hash configured successfully"
fi

# Wait for ClickHouse process
wait $CLICKHOUSE_PID