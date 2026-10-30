#!/bin/sh
set -eu

task_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$task_root"
task_project=${LLM_PLATFORM_TEST_PROJECT:-llm-platform-validation-$$}

compose() {
    docker compose -p "$task_project" -f compose.test.yaml "$@"
}

cleanup() {
    task_status=$?
    trap - EXIT
    if [ "$task_status" -ne 0 ]; then
        compose logs --tail 80
    fi
    compose down --volumes --remove-orphans
    exit "$task_status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

compose build api llm-proxy mcp exporter
compose up -d --wait --wait-timeout 240 api llm-proxy mcp exporter
# A second startup must reuse the configured admin without duplicate seed data.
compose restart api
compose up -d --wait --wait-timeout 120 api
compose run --rm tests
