#!/bin/sh
# collect_logs.sh (sh 호환 버전)

LOG_DIR="/logs"
INTERVAL=${INTERVAL:-1800}
RETENTION_DAYS=${RETENTION_DAYS:-30}
WATCH_CONTAINERS=${WATCH_CONTAINERS:-""}

echo "🚀 Starting Shell log collector..."
echo "📁 Log directory: $LOG_DIR"
echo "⏱️  Interval: ${INTERVAL}s ($((INTERVAL/60))min)"
echo "🗑️  Retention: ${RETENTION_DAYS} days"

if [ -n "$WATCH_CONTAINERS" ]; then
    echo "🎯 Watching: $WATCH_CONTAINERS"
else
    echo "🎯 Watching: ALL containers"
fi

# 오래된 로그 파일 삭제 함수
cleanup_old_logs() {
    cutoff_timestamp=$(($(date +%s) - RETENTION_DAYS * 86400))
    cutoff_date=$(date -d "@$cutoff_timestamp" +%Y%m%d 2>/dev/null)

    if [ -z "$cutoff_date" ]; then
        echo "⚠️  Failed to calculate cutoff date"
        return
    fi

    deleted=0

    for container_dir in "$LOG_DIR"/*; do
        [ -d "$container_dir" ] || continue

        for file in "$container_dir"/*.txt; do
            [ -f "$file" ] || continue

            filename=$(basename "$file")
            date_part=$(echo "$filename" | sed -n 's/^\([0-9]\{8\}\)\.txt$/\1/p')

            # date_part가 비어있지 않고 cutoff_date보다 작은 경우에만 삭제
            if [ -n "$date_part" ] && [ "$date_part" -lt "$cutoff_date" ] 2>/dev/null; then
                rm -f "$file"
                echo "🗑️  Deleted: $(basename "$container_dir")/$filename"
                deleted=$((deleted + 1))
            fi
        done

        if [ -z "$(ls -A "$container_dir" 2>/dev/null)" ]; then
            rmdir "$container_dir"
            echo "🗑️  Removed empty directory: $(basename "$container_dir")"
        fi
    done

    if [ $deleted -gt 0 ]; then
        echo "🗑️  Cleaned up $deleted old log files"
    fi
}

# 로그 수집 함수
collect_logs() {
    today=$(date +%Y%m%d)

    # 감시할 컨테이너 목록
    if [ -n "$WATCH_CONTAINERS" ]; then
        # IFS를 사용한 split (sh 호환)
        OLD_IFS="$IFS"
        IFS=','
        set -- $WATCH_CONTAINERS
        IFS="$OLD_IFS"
        containers="$@"
    else
        containers=$(docker ps --format '{{.Names}}')
    fi

    for container in $containers; do
        container=$(echo "$container" | xargs)

        # 컨테이너가 실행 중인지 확인
        if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            continue
        fi

        echo "📝 Collecting logs from: $container"

        # 컨테이너별 디렉토리 생성
        container_dir="$LOG_DIR/$container"
        mkdir -p "$container_dir"

        # 날짜.txt 형식으로 저장
        filename="$container_dir/${today}.txt"

        # 파일 생성 (sh 호환 방식)
        echo "Container: $container" > "$filename"
        echo "Container ID: $(docker inspect -f '{{.Id}}' "$container" 2>/dev/null || echo 'N/A')" >> "$filename"
        echo "Image: $(docker inspect -f '{{.Config.Image}}' "$container" 2>/dev/null || echo 'N/A')" >> "$filename"
        echo "Status: $(docker inspect -f '{{.State.Status}}' "$container" 2>/dev/null || echo 'N/A')" >> "$filename"
        echo "Collected at: $(date '+%Y-%m-%d %H:%M:%S')" >> "$filename"
        echo "================================================================================" >> "$filename"
        echo "" >> "$filename"
        docker logs --timestamps --tail 1000 "$container" >> "$filename" 2>&1

        echo "✓ Saved: $container/${today}.txt"
    done
}

# 메인 루프
while true; do
    collect_logs
    cleanup_old_logs
    echo "✅ Log collection completed"
    echo "💤 Sleeping for $((INTERVAL/60)) minutes..."
    sleep "$INTERVAL"
done