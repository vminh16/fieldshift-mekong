#!/usr/bin/env bash
set -euo pipefail
curl --fail --silent --show-error http://localhost:8000/v1/health
printf '\n'
status="$(curl -s -o /dev/null -w '%{http_code}' -X POST http://localhost:8000/v1/plans)"
if [[ "$status" != "501" ]]; then
  echo "Expected scaffold planning response 501, received $status" >&2
  exit 1
fi
echo 'API scaffold smoke test OK'
